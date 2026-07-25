"""使用者管理（僅管理員）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import require_admin
from services import user_service

router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserUpdateIn(BaseModel):
    password: str | None = None
    is_admin: bool | None = None


@router.get("")
def list_users(admin: dict = Depends(require_admin)):
    return user_service.list_users()


@router.post("")
def create_user(body: UserIn, admin: dict = Depends(require_admin)):
    try:
        return user_service.create_user(body.username, body.password, body.is_admin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}")
def update_user(user_id: int, body: UserUpdateIn, admin: dict = Depends(require_admin)):
    try:
        user_service.update_user(user_id, password=body.password, is_admin=body.is_admin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    try:
        user_service.delete_user(user_id, acting_user_id=admin["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
