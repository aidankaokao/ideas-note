from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import insert, select

from config import settings
from db.engine import engine
from db.tables import users


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def authenticate(username: str, password: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.username == username)).first()
    if row is None:
        return None
    user = dict(row._mapping)
    if not verify_password(password, user["password_hash"]):
        return None
    user.pop("password_hash")
    return user


def seed_admin() -> None:
    """第一次啟動（無任何使用者）時建立預設管理員 admin/admin，登入後請儘快改密碼。"""
    with engine.begin() as conn:
        exists = conn.execute(select(users.c.id).limit(1)).first()
        if exists is None:
            conn.execute(
                insert(users).values(
                    username="admin",
                    password_hash=hash_password("admin"),
                    is_admin=True,
                )
            )
