"""心智圖（保存供心智圖頁查看 / 編輯 / 重新生成 / 下載）。"""

from sqlalchemy import delete, insert, select, update

from db.engine import engine
from db.tables import mindmaps


def list_mindmaps(user_id: int) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            select(mindmaps).where(mindmaps.c.user_id == user_id).order_by(mindmaps.c.id.desc())
        )
        return [dict(r._mapping) for r in rows]


def get_mindmap(user_id: int, mindmap_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            select(mindmaps).where(
                mindmaps.c.id == mindmap_id, mindmaps.c.user_id == user_id
            )
        ).first()
    return dict(row._mapping) if row else None


def create_mindmap(
    user_id: int,
    title: str,
    markdown: str,
    topic_id: int | None = None,
    query: str | None = None,
) -> dict:
    with engine.begin() as conn:
        mid = conn.execute(
            insert(mindmaps).values(
                user_id=user_id, title=title[:200], markdown=markdown,
                topic_id=topic_id, query=(query or None),
            )
        ).inserted_primary_key[0]
    return {"id": mid, "title": title[:200]}


def update_mindmap(user_id: int, mindmap_id: int, title: str, markdown: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            update(mindmaps)
            .where(mindmaps.c.id == mindmap_id, mindmaps.c.user_id == user_id)
            .values(title=title[:200], markdown=markdown)
        )


def delete_mindmap(user_id: int, mindmap_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(mindmaps).where(
                mindmaps.c.id == mindmap_id, mindmaps.c.user_id == user_id
            )
        )
