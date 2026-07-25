"""筆記向量化與相似度檢索（cosine，存 notes.embedding JSON 欄位）。"""

import math

from sqlalchemy import select, update

from db.engine import engine
from db.tables import notes
from llm import get_embedding_model


def embed_text(user_id: int, text: str) -> list[float]:
    model = get_embedding_model(user_id)
    return model.embed_query(text[:6000])


def try_embed_note(user_id: int, note_id: int, title: str, content: str) -> bool:
    """筆記存檔後盡力補向量；失敗（尚未選 embedding provider / 網路錯）不擋筆記操作。"""
    try:
        vec = embed_text(user_id, f"{title}\n{content}")
    except Exception:  # noqa: BLE001 - 向量化失敗不影響筆記本身
        return False
    with engine.begin() as conn:
        conn.execute(update(notes).where(notes.c.id == note_id).values(embedding=vec))
    return True


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def similar_notes(
    user_id: int,
    query_vec: list[float],
    exclude_note_id: int | None = None,
    top_k: int = 5,
    min_score: float = 0.25,
) -> list[dict]:
    """對該使用者所有已向量化筆記算 cosine，回前 top_k 筆（含 score，去掉 embedding）。"""
    with engine.connect() as conn:
        rows = conn.execute(select(notes).where(notes.c.user_id == user_id)).fetchall()
    scored = []
    for row in rows:
        n = dict(row._mapping)
        if exclude_note_id is not None and n["id"] == exclude_note_id:
            continue
        if not n.get("embedding"):
            continue
        score = cosine(query_vec, n["embedding"])
        if score >= min_score:
            n.pop("embedding")
            n["score"] = round(score, 3)
            scored.append(n)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
