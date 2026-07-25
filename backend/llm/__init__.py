"""LLM 工廠（有前端版：從 DB 讀「該帳號」在設定頁註冊、選用的 provider）。
上層（services / LangGraph node）一律從這裡建構，不直接 new class。
見 reference/backend/llm-integration.md §3、§5。
"""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from services.provider_service import get_active_provider, get_provider


def _resolve(user_id: int, provider_id: int | None, purpose: str) -> dict:
    if provider_id is not None:
        cfg = get_provider(user_id, provider_id)
        if cfg is None:
            raise ValueError(f"找不到 provider id={provider_id}")
        return cfg
    return get_active_provider(user_id, purpose)


def get_chat_model(
    user_id: int,
    provider_id: int | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """provider_id 省略時用該帳號設定頁選用（active）的「對話」那筆。"""
    cfg = _resolve(user_id, provider_id, "chat")
    temp = cfg.get("temperature", 0.7) if temperature is None else temperature

    if cfg["provider"] == "ollama":
        return ChatOllama(model=cfg["model"], base_url=cfg["base_url"], temperature=temp)
    if cfg["provider"] == "openai":  # 外部 OpenAI 或本地 vLLM（OpenAI 相容 API）
        return ChatOpenAI(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",
            temperature=temp,
        )
    raise ValueError(f"未知的 provider: {cfg['provider']!r}")


def get_embedding_model(user_id: int, provider_id: int | None = None) -> Embeddings:
    """provider_id 省略時用該帳號設定頁選用（active）的「embedding」那筆。"""
    cfg = _resolve(user_id, provider_id, "embedding")

    if cfg["provider"] == "ollama":
        return OllamaEmbeddings(model=cfg["model"], base_url=cfg["base_url"])
    if cfg["provider"] == "openai":
        return OpenAIEmbeddings(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",
        )
    raise ValueError(f"未知的 provider: {cfg['provider']!r}")
