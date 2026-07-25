"""路由共用依賴：JWT 驗證與管理員權限。"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from db.engine import engine
from db.tables import users
from services.auth_service import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="未登入")
    user_id = decode_token(cred.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="登入逾期，請重新登入")
    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).first()
    if row is None:
        raise HTTPException(status_code=401, detail="帳號不存在")
    user = dict(row._mapping)
    user.pop("password_hash")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    return user
