"""LLM provider 設定（每帳號各自註冊多筆、各自選用；見 reference/backend/llm-integration.md §5）。"""

import httpx
from sqlalchemy import delete, insert, select, update

from db.engine import engine
from db.tables import app_settings, llm_providers

ACTIVE_KEYS = {"chat": "active_chat_provider_id", "embedding": "active_embedding_provider_id"}


def _active_key(purpose: str, user_id: int) -> str:
    return f"{ACTIVE_KEYS[purpose]}:{user_id}"


def _mask_key(key: str) -> str:
    if not key:
        return ""
    return f"{key[:3]}****{key[-4:]}" if len(key) > 10 else "****"


def list_providers(user_id: int) -> list[dict]:
    """列表用：api_key 遮罩，不回明文給前端。"""
    with engine.connect() as conn:
        rows = conn.execute(
            select(llm_providers)
            .where(llm_providers.c.user_id == user_id)
            .order_by(llm_providers.c.id)
        )
        result = []
        for r in rows:
            p = dict(r._mapping)
            p["api_key"] = _mask_key(p["api_key"])
            result.append(p)
    return result


def get_provider(user_id: int, provider_id: int) -> dict | None:
    """內部用：含明文 api_key，僅供建構 LLM，不可直接回給前端。"""
    with engine.connect() as conn:
        row = conn.execute(
            select(llm_providers).where(
                llm_providers.c.id == provider_id, llm_providers.c.user_id == user_id
            )
        ).first()
    return dict(row._mapping) if row else None


def create_provider(user_id: int, data: dict) -> int:
    with engine.begin() as conn:
        return conn.execute(
            insert(llm_providers).values(user_id=user_id, **data)
        ).inserted_primary_key[0]


def update_provider(user_id: int, provider_id: int, data: dict) -> None:
    data = dict(data)
    if not data.get("api_key"):
        data.pop("api_key", None)  # 前端沒送新 key 就保留舊值
    with engine.begin() as conn:
        conn.execute(
            update(llm_providers)
            .where(llm_providers.c.id == provider_id, llm_providers.c.user_id == user_id)
            .values(**data)
        )


def delete_provider(user_id: int, provider_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(llm_providers).where(
                llm_providers.c.id == provider_id, llm_providers.c.user_id == user_id
            )
        )
    for purpose in ACTIVE_KEYS:
        if get_setting(_active_key(purpose, user_id)) == str(provider_id):
            set_setting(_active_key(purpose, user_id), "")


def get_setting(key: str) -> str:
    with engine.connect() as conn:
        row = conn.execute(select(app_settings.c.value).where(app_settings.c.key == key)).first()
    return row[0] if row else ""


def set_setting(key: str, value: str) -> None:
    with engine.begin() as conn:
        if conn.execute(select(app_settings.c.key).where(app_settings.c.key == key)).first():
            conn.execute(update(app_settings).where(app_settings.c.key == key).values(value=value))
        else:
            conn.execute(insert(app_settings).values(key=key, value=value))


def get_active_ids(user_id: int) -> dict:
    result = {}
    for purpose in ACTIVE_KEYS:
        raw = get_setting(_active_key(purpose, user_id))
        result[f"{purpose}_provider_id"] = int(raw) if raw else None
    return result


def set_active(user_id: int, purpose: str, provider_id: int | None) -> None:
    set_setting(_active_key(purpose, user_id), "" if provider_id is None else str(provider_id))


def get_active_provider(user_id: int, purpose: str = "chat") -> dict:
    """給 llm/ 工廠讀「該帳號目前選用」的那筆設定；未設定時丟出可讀訊息。"""
    label = "對話" if purpose == "chat" else "embedding"
    raw = get_setting(_active_key(purpose, user_id))
    if not raw:
        raise ValueError(f"尚未選用{label}模型：請到「設定」頁註冊 LLM provider 並選用")
    cfg = get_provider(user_id, int(raw))
    if cfg is None:
        raise ValueError(f"選用的{label} provider 已被刪除，請到「設定」頁重新選擇")
    return cfg


def clear_user_settings(user_id: int) -> None:
    """刪帳號時清掉其 provider 與選用設定。"""
    with engine.begin() as conn:
        conn.execute(delete(llm_providers).where(llm_providers.c.user_id == user_id))
        keys = [_active_key(p, user_id) for p in ACTIVE_KEYS]
        conn.execute(delete(app_settings).where(app_settings.c.key.in_(keys)))


def test_connection(cfg: dict) -> dict:
    """設定頁「測試連線」：列模型清單確認 base_url / key 可用，回 {ok, message}。"""
    base = (cfg.get("base_url") or "").rstrip("/")
    if not base:
        return {"ok": False, "message": "base_url 不可為空"}
    try:
        if cfg.get("provider") == "ollama":
            resp = httpx.get(f"{base}/api/tags", timeout=10)
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
        else:
            headers = {"Authorization": f"Bearer {cfg.get('api_key') or 'EMPTY'}"}
            resp = httpx.get(f"{base}/models", headers=headers, timeout=10)
            resp.raise_for_status()
            models = [m.get("id") for m in resp.json().get("data", [])]
    except httpx.HTTPStatusError as e:
        return {"ok": False, "message": f"連線失敗：HTTP {e.response.status_code}（請檢查 API key / base_url）"}
    except Exception as e:  # noqa: BLE001 - 網路錯誤種類多，統一回訊息
        return {"ok": False, "message": f"連線失敗：{e}"}

    model = cfg.get("model")
    if model and models and model not in models:
        return {"ok": True, "message": f"連線成功，但模型清單中找不到「{model}」（共 {len(models)} 個模型可用）"}
    return {"ok": True, "message": f"連線成功（{len(models)} 個模型可用）"}
