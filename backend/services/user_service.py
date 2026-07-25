"""使用者管理（管理員用）。規則錯誤一律 raise ValueError，由 router 轉 400。"""

from sqlalchemy import delete, insert, select, update

from db.engine import engine
from db.tables import (
    briefings,
    chat_messages,
    chat_summaries,
    mindmaps,
    note_links,
    note_topics,
    notes,
    topics,
    users,
)
from services.auth_service import hash_password
from services.provider_service import clear_user_settings


def list_users() -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            select(users.c.id, users.c.username, users.c.is_admin, users.c.created_at)
            .order_by(users.c.id)
        )
        return [dict(r._mapping) for r in rows]


def create_user(username: str, password: str, is_admin: bool = False) -> dict:
    username = username.strip()
    if not username or not password:
        raise ValueError("帳號與密碼不可為空")
    with engine.begin() as conn:
        dup = conn.execute(select(users.c.id).where(users.c.username == username)).first()
        if dup is not None:
            raise ValueError("帳號已存在")
        uid = conn.execute(
            insert(users).values(
                username=username,
                password_hash=hash_password(password),
                is_admin=is_admin,
            )
        ).inserted_primary_key[0]
    return {"id": uid, "username": username, "is_admin": is_admin}


def update_user(user_id: int, password: str | None = None, is_admin: bool | None = None) -> None:
    values: dict = {}
    if password:
        values["password_hash"] = hash_password(password)
    if is_admin is not None:
        values["is_admin"] = is_admin
    if not values:
        return
    with engine.begin() as conn:
        if is_admin is False:
            other_admin = conn.execute(
                select(users.c.id).where(users.c.is_admin.is_(True), users.c.id != user_id)
            ).first()
            if other_admin is None:
                raise ValueError("至少要保留一個管理員")
        conn.execute(update(users).where(users.c.id == user_id).values(**values))


def delete_user(user_id: int, acting_user_id: int) -> None:
    if user_id == acting_user_id:
        raise ValueError("不能刪除自己")
    with engine.begin() as conn:
        row = conn.execute(select(users.c.is_admin).where(users.c.id == user_id)).first()
        if row is None:
            raise ValueError("找不到使用者")
        if row[0]:
            other_admin = conn.execute(
                select(users.c.id).where(users.c.is_admin.is_(True), users.c.id != user_id)
            ).first()
            if other_admin is None:
                raise ValueError("至少要保留一個管理員")

        # 連同該使用者的所有資料一併刪除（筆記/連結/主題/對話/心智圖/簡報）
        nids = [r[0] for r in conn.execute(select(notes.c.id).where(notes.c.user_id == user_id))]
        if nids:
            conn.execute(delete(note_topics).where(note_topics.c.note_id.in_(nids)))
        tids = [r[0] for r in conn.execute(select(topics.c.id).where(topics.c.user_id == user_id))]
        if tids:
            conn.execute(delete(note_topics).where(note_topics.c.topic_id.in_(tids)))
            conn.execute(delete(topics).where(topics.c.user_id == user_id))
        conn.execute(delete(note_links).where(note_links.c.user_id == user_id))
        conn.execute(delete(notes).where(notes.c.user_id == user_id))
        conn.execute(delete(chat_messages).where(chat_messages.c.user_id == user_id))
        conn.execute(delete(chat_summaries).where(chat_summaries.c.user_id == user_id))
        conn.execute(delete(mindmaps).where(mindmaps.c.user_id == user_id))
        conn.execute(delete(briefings).where(briefings.c.user_id == user_id))
        conn.execute(delete(users).where(users.c.id == user_id))
    clear_user_settings(user_id)  # LLM provider 與選用設定也跟著帳號刪
