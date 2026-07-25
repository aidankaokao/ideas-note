"""導師對話記錄（存 DB，跨裝置/重整可續聊）＋上下文壓縮摘要。"""

from sqlalchemy import delete, insert, select, update

from db.engine import engine
from db.tables import chat_messages, chat_summaries


def history(user_id: int, thread: str, limit: int = 50) -> list[dict]:
    """回傳該 thread 最近 limit 則訊息（時間正序，含 id）。"""
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                chat_messages.c.id, chat_messages.c.role,
                chat_messages.c.content, chat_messages.c.payload,
            )
            .where(chat_messages.c.user_id == user_id, chat_messages.c.thread == thread)
            .order_by(chat_messages.c.id.desc())
            .limit(limit)
        ).fetchall()
    return [dict(r._mapping) for r in reversed(rows)]


def history_after(user_id: int, thread: str, after_id: int, limit: int = 100) -> list[dict]:
    """摘要覆蓋點之後的訊息（給 LLM 上下文用）。"""
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                chat_messages.c.id, chat_messages.c.role,
                chat_messages.c.content, chat_messages.c.payload,
            )
            .where(
                chat_messages.c.user_id == user_id,
                chat_messages.c.thread == thread,
                chat_messages.c.id > after_id,
            )
            .order_by(chat_messages.c.id)
            .limit(limit)
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def append(user_id: int, thread: str, role: str, content: str, payload: dict | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(chat_messages).values(
                user_id=user_id, thread=thread, role=role, content=content, payload=payload
            )
        )


def clear(user_id: int, thread: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(chat_messages).where(
                chat_messages.c.user_id == user_id, chat_messages.c.thread == thread
            )
        )
        conn.execute(
            delete(chat_summaries).where(
                chat_summaries.c.user_id == user_id, chat_summaries.c.thread == thread
            )
        )


def get_summary(user_id: int, thread: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            select(chat_summaries.c.summary, chat_summaries.c.covered_until_id).where(
                chat_summaries.c.user_id == user_id, chat_summaries.c.thread == thread
            )
        ).first()
    if row is None:
        return {"summary": "", "covered_until_id": 0}
    return dict(row._mapping)


def set_summary(user_id: int, thread: str, summary: str, covered_until_id: int) -> None:
    with engine.begin() as conn:
        exists = conn.execute(
            select(chat_summaries.c.user_id).where(
                chat_summaries.c.user_id == user_id, chat_summaries.c.thread == thread
            )
        ).first()
        if exists:
            conn.execute(
                update(chat_summaries)
                .where(chat_summaries.c.user_id == user_id, chat_summaries.c.thread == thread)
                .values(summary=summary, covered_until_id=covered_until_id)
            )
        else:
            conn.execute(
                insert(chat_summaries).values(
                    user_id=user_id, thread=thread,
                    summary=summary, covered_until_id=covered_until_id,
                )
            )
