"""LLM provider 設定頁 API（每帳號各自一套；見 reference/backend/llm-integration.md §5）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_current_user
from services import provider_service

router = APIRouter(prefix="/settings", tags=["settings"])


class ProviderIn(BaseModel):
    name: str
    provider: str = "openai"  # openai / ollama
    base_url: str = "https://api.openai.com/v1"
    model: str
    api_key: str = ""
    temperature: float = 0.7


class TestIn(BaseModel):
    id: int | None = None  # 帶 id 且未填新 key 時，用已存的 key 測試
    provider: str = "openai"
    base_url: str = ""
    model: str = ""
    api_key: str = ""


class ActiveIn(BaseModel):
    chat_provider_id: int | None = None
    embedding_provider_id: int | None = None


@router.get("/llm-providers")
def list_providers(user: dict = Depends(get_current_user)):
    return provider_service.list_providers(user["id"])


@router.post("/llm-providers")
def create_provider(body: ProviderIn, user: dict = Depends(get_current_user)):
    if body.provider not in ("openai", "ollama"):
        raise HTTPException(status_code=400, detail="provider 必須是 openai 或 ollama")
    provider_id = provider_service.create_provider(user["id"], body.model_dump())
    return {"id": provider_id}


@router.put("/llm-providers/{provider_id}")
def update_provider(provider_id: int, body: ProviderIn, user: dict = Depends(get_current_user)):
    if provider_service.get_provider(user["id"], provider_id) is None:
        raise HTTPException(status_code=404, detail="找不到 provider")
    provider_service.update_provider(user["id"], provider_id, body.model_dump())
    return {"ok": True}


@router.delete("/llm-providers/{provider_id}")
def delete_provider(provider_id: int, user: dict = Depends(get_current_user)):
    provider_service.delete_provider(user["id"], provider_id)
    return {"ok": True}


@router.post("/llm-providers/test")
def test_provider(body: TestIn, user: dict = Depends(get_current_user)):
    cfg = body.model_dump()
    if body.id and not body.api_key:
        stored = provider_service.get_provider(user["id"], body.id)
        if stored:
            cfg["api_key"] = stored["api_key"]
    return provider_service.test_connection(cfg)


@router.get("/llm-active")
def get_active(user: dict = Depends(get_current_user)):
    return provider_service.get_active_ids(user["id"])


@router.put("/llm-active")
def set_active(body: ActiveIn, user: dict = Depends(get_current_user)):
    provider_service.set_active(user["id"], "chat", body.chat_provider_id)
    provider_service.set_active(user["id"], "embedding", body.embedding_provider_id)
    return provider_service.get_active_ids(user["id"])
