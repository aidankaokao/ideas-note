"""靈感筆記 CRUD、相關筆記檢索、筆記間連結。"""

import threading

from sqlalchemy import delete, func, insert, or_, select, update

from db.engine import engine
from db.tables import note_links, note_topics, notes
from services import embedding_service

# 列表不撈 embedding（1536 維浮點數，量大時 payload 很肥）
_LIST_COLS = (
    notes.c.id,
    notes.c.title,
    notes.c.content,
    notes.c.source,
    notes.c.created_at,
    notes.c.updated_at,
)


def _strip(row) -> dict:
    n = dict(row._mapping)
    n["has_embedding"] = bool(n.get("embedding"))
    n.pop("embedding", None)
    return n


def list_notes(user_id: int, q: str | None = None) -> list[dict]:
    stmt = (
        select(*_LIST_COLS)
        .where(notes.c.user_id == user_id)
        .order_by(notes.c.updated_at.desc())
    )
    if q:
        stmt = stmt.where(or_(notes.c.title.ilike(f"%{q}%"), notes.c.content.ilike(f"%{q}%")))
    with engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(stmt)]


def get_note(user_id: int, note_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            select(notes).where(notes.c.id == note_id, notes.c.user_id == user_id)
        ).first()
    return _strip(row) if row else None


def _auto_classify(user_id: int, note_id: int) -> None:
    """背景把新筆記融入知識體系；任何失敗（LLM 未設定等）都不影響筆記。"""
    try:
        from services import topic_service

        topic_service.classify_note(user_id, note_id)
    except Exception:  # noqa: BLE001
        pass


def create_note(user_id: int, title: str, content: str, source: str = "manual") -> dict:
    with engine.begin() as conn:
        note_id = conn.execute(
            insert(notes).values(user_id=user_id, title=title, content=content, source=source)
        ).inserted_primary_key[0]
    embedding_service.try_embed_note(user_id, note_id, title, content)
    # 背景自動歸入知識體系主題，不拖慢「記筆記」的回應
    threading.Thread(target=_auto_classify, args=(user_id, note_id), daemon=True).start()
    return get_note(user_id, note_id)


def update_note(user_id: int, note_id: int, title: str, content: str) -> dict | None:
    with engine.begin() as conn:
        conn.execute(
            update(notes)
            .where(notes.c.id == note_id, notes.c.user_id == user_id)
            .values(title=title, content=content, updated_at=func.now())
        )
    embedding_service.try_embed_note(user_id, note_id, title, content)
    return get_note(user_id, note_id)


def delete_note(user_id: int, note_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(note_links).where(
                note_links.c.user_id == user_id,
                or_(note_links.c.from_note_id == note_id, note_links.c.to_note_id == note_id),
            )
        )
        conn.execute(delete(note_topics).where(note_topics.c.note_id == note_id))
        conn.execute(delete(notes).where(notes.c.id == note_id, notes.c.user_id == user_id))


def related_notes(user_id: int, note_id: int, top_k: int = 5) -> list[dict]:
    """用 embedding 找相似筆記；沒有向量就當場補算一次。"""
    with engine.connect() as conn:
        row = conn.execute(
            select(notes).where(notes.c.id == note_id, notes.c.user_id == user_id)
        ).first()
    if row is None:
        raise ValueError("找不到筆記")
    n = dict(row._mapping)
    vec = n.get("embedding")
    if not vec:
        if not embedding_service.try_embed_note(user_id, note_id, n["title"], n["content"]):
            raise ValueError("此筆記還沒有向量：請先到「設定」頁註冊並選用 embedding provider")
        with engine.connect() as conn:
            vec = conn.execute(select(notes.c.embedding).where(notes.c.id == note_id)).scalar_one()
    return embedding_service.similar_notes(user_id, vec, exclude_note_id=note_id, top_k=top_k)


# ── 筆記間連結 ──────────────────────────────────────────────


def list_links(user_id: int, note_id: int) -> list[dict]:
    """回該筆記的雙向連結，含對方標題。"""
    result = []
    with engine.connect() as conn:
        out_rows = conn.execute(
            select(note_links, notes.c.title)
            .join(notes, notes.c.id == note_links.c.to_note_id)
            .where(note_links.c.user_id == user_id, note_links.c.from_note_id == note_id)
        )
        for r in out_rows:
            m = r._mapping
            result.append({
                "id": m["id"], "other_note_id": m["to_note_id"], "other_title": m["title"],
                "reason": m["reason"], "direction": "out",
            })
        in_rows = conn.execute(
            select(note_links, notes.c.title)
            .join(notes, notes.c.id == note_links.c.from_note_id)
            .where(note_links.c.user_id == user_id, note_links.c.to_note_id == note_id)
        )
        for r in in_rows:
            m = r._mapping
            result.append({
                "id": m["id"], "other_note_id": m["from_note_id"], "other_title": m["title"],
                "reason": m["reason"], "direction": "in",
            })
    return result


def create_link(user_id: int, from_note_id: int, to_note_id: int, reason: str = "") -> None:
    if from_note_id == to_note_id:
        raise ValueError("不能連結到自己")
    with engine.begin() as conn:
        for nid in (from_note_id, to_note_id):
            ok = conn.execute(
                select(notes.c.id).where(notes.c.id == nid, notes.c.user_id == user_id)
            ).first()
            if ok is None:
                raise ValueError("找不到筆記")
        dup = conn.execute(
            select(note_links.c.id).where(
                or_(
                    (note_links.c.from_note_id == from_note_id) & (note_links.c.to_note_id == to_note_id),
                    (note_links.c.from_note_id == to_note_id) & (note_links.c.to_note_id == from_note_id),
                )
            )
        ).first()
        if dup is not None:
            raise ValueError("這兩篇筆記已建立過連結")
        conn.execute(
            insert(note_links).values(
                user_id=user_id, from_note_id=from_note_id, to_note_id=to_note_id, reason=reason
            )
        )


def delete_link(user_id: int, link_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(note_links).where(note_links.c.id == link_id, note_links.c.user_id == user_id)
        )
