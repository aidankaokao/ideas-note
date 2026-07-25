from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_current_user
from services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    password: str


@router.post("/login")
def login(body: LoginIn):
    user = auth_service.authenticate(body.username.strip(), body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    return {"token": auth_service.create_token(user["id"]), "user": user}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.put("/password")
def change_password(body: PasswordIn, user: dict = Depends(get_current_user)):
    if len(body.password) < 4:
        raise HTTPException(status_code=400, detail="密碼至少 4 碼")
    user_service.update_user(user["id"], password=body.password)
    return {"ok": True}
