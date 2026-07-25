# LLM 串接慣例（ChatOllama / ChatOpenAI · 可攜式）

> 專案用到 LLM 時的統一建構方式。**同時支援兩種後端**：
> - **`langchain_ollama.ChatOllama`** — 呼叫本地架設的 **Ollama server** 託管的模型。
> - **`langchain_openai.ChatOpenAI`** — 呼叫**外部 OpenAI 模型**，或**未來本地架設的 vLLM** 託管模型（vLLM 提供 OpenAI 相容 API，故用 `ChatOpenAI` 指到 vLLM 的 base_url 即可）。
>
> 兩者都回傳 LangChain 的 chat model 介面（`.invoke` / `.stream` / `.bind_tools`），所以上層（含 `langgraph-agent.md` 的 node）用起來一致、可互換。

---

## 0. 一句話總結

寫一個 **`get_chat_model()` 工廠**，依設定回傳 `ChatOllama`（本地 Ollama）或 `ChatOpenAI`（外部 OpenAI / 本地 vLLM）。上層只呼叫工廠，**不直接 new 特定 class**，也不寫死 base_url / model。

**設定「來源」依專案有沒有前端而不同（見 §0.1）——但工廠介面不變**：不管設定從 `.env` 或從資料庫來，`get_chat_model()` 對上層都一樣。

---

## 0.1 設定放哪：有前端 vs 無前端（先決定這個）

LLM provider 的**設定來源**分兩種情況，先判斷這個專案屬於哪種：

| 情況 | provider 設定放哪 | 誰維護 | 怎麼做 |
|---|---|---|---|
| **有前端**（有設計設定頁）| **資料庫**（可註冊多個 provider）| **使用者**在設定頁自行註冊 / 增刪 | 見 §5：設定頁 CRUD 多個 provider，專案再選要用哪個；**細節留給接手的 session 依開發者需求設計** |
| **無前端**（純後端 / CLI / 服務）| **`.env`**（單一組或少數幾組）| **開發者**改檔 | 見 §2：`.env` + `config.py` |

- **有前端** → 不要把 provider 寫死在 `.env`；改成「使用者在**設定頁**註冊，可一次註冊多個（多把 key / 多個 base_url / 多個模型），依專案配置選用」。UI 與資料表細節**不在這份文件硬性規定**，交給實作的 Claude Code session 依當前開發者需求設計，只要遵守 §5 的原則與 §3 工廠介面即可。
- **無前端** → 維持 §2 的 `.env` 方式，開發者直接改檔切換。

> 判準：**這個專案有沒有給使用者操作的設定頁？有 → §5（前端註冊多 provider）；沒有 → §2（.env）。**

---

## 1. 依賴

```txt
langchain-core>=0.3
langchain-ollama>=0.2     # ChatOllama
langchain-openai>=0.2     # ChatOpenAI
```

import 寫法（固定）：

```python
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
```

---

## 2. 設定：無前端用 `.env`（延伸 config.py）

> **適用「無前端」專案**（見 §0.1）。有前端請改看 §5，provider 存資料庫由使用者在設定頁註冊。

在 `config.py` 的 `Settings` 加 LLM 相關欄位（承 `backend-conventions.md` §5）：

```python
# backend/config.py（節錄）
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 選哪個後端：ollama | openai
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"          # provider 對應的模型名
    llm_temperature: float = 0.0

    # 本地 Ollama
    ollama_base_url: str = "http://localhost:11434"

    # OpenAI 或本地 vLLM（vLLM 走 OpenAI 相容 API）
    openai_base_url: str = "https://api.openai.com/v1"   # vLLM 時改成 http://vllm-host:8000/v1
    openai_api_key: str = ""                              # vLLM 常可填任意值如 "EMPTY"
```

`.env` 範例：

```dotenv
# 本地 Ollama
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434

# 外部 OpenAI（切換時）
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

# 本地 vLLM（OpenAI 相容；切換時）
# LLM_PROVIDER=openai
# LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
# OPENAI_BASE_URL=http://vllm-host:8000/v1
# OPENAI_API_KEY=EMPTY
```

> **重點**：外部 OpenAI 與本地 vLLM 都用 `openai` provider，差別只在 `OPENAI_BASE_URL`（指到 OpenAI 官方 or vLLM host）。切換不改程式，只改 `.env`。

---

## 3. 工廠函式（唯一建構入口）

```python
# backend/llm/__init__.py
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from config import settings


@lru_cache
def get_chat_model(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """回傳 LangChain chat model；上層一律用這個，不直接 new class。

    provider="ollama" -> 本地 Ollama server 託管模型
    provider="openai" -> 外部 OpenAI 或本地 vLLM（OpenAI 相容 API）
    """
    provider = provider or settings.llm_provider
    model = model or settings.llm_model
    temperature = settings.llm_temperature if temperature is None else temperature

    if provider == "ollama":
        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    if provider == "openai":
        # 外部 OpenAI 或本地 vLLM：差別只在 base_url / api_key
        return ChatOpenAI(
            model=model,
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key or "EMPTY",  # vLLM 常不驗 key
            temperature=temperature,
        )

    raise ValueError(f"未知的 llm_provider: {provider!r}")
```

---

## 4. 用法（invoke / stream / tools 都一致）

```python
from langchain_core.messages import SystemMessage, HumanMessage

from llm import get_chat_model

llm = get_chat_model()   # 依 .env 決定是 Ollama 還是 OpenAI/vLLM

# 單次
resp = llm.invoke([
    SystemMessage(content="你是簡潔的助理。"),
    HumanMessage(content="用一句話介紹台灣。"),
])
print(resp.content)

# 串流（接 FastAPI SSE / StreamingResponse）
for chunk in llm.stream([HumanMessage(content="寫首短詩")]):
    print(chunk.content, end="", flush=True)

# 綁工具（給 LangGraph agent 用，見 langgraph-agent.md §5）
llm_with_tools = llm.bind_tools([my_tool])
```

因為 `ChatOllama` 與 `ChatOpenAI` 都實作同一介面，**切換 provider 完全不動上層 / agent 程式**。

---

## 5. 有前端：使用者在設定頁註冊多個 provider（存資料庫）

> **適用「有前端」專案**（見 §0.1）。此時**不要**把 provider 寫死在 `.env`，改成使用者在**設定頁自行註冊**，可一次註冊多個，專案再依配置選要用哪一個。
>
> **UI 版面與資料表欄位細節不在此硬性規定** —— 交給接手的 Claude Code session 依當前開發者需求設計。本節只定「原則」與「必須對齊工廠介面」，避免各專案亂長。

### 5.1 原則

- **多筆註冊**：使用者可在設定頁新增 / 編輯 / 刪除**多個** provider 設定（如：一個本地 Ollama、一個外部 OpenAI、一個本地 vLLM），各自獨立存。
- **一筆 = 一組可用配置**：每筆至少含 `provider`（ollama / openai）、`base_url`、`model`、`api_key`（openai 類需要）、以及一個好認的**顯示名稱 / id**。
- **專案選用**：另存一個「目前選用哪一筆」的設定（active provider id），可以是全域一個，或依用途分（如 chat / embedding 各選一筆）——依開發者需求決定。
- **金鑰安全**：`api_key` 存後端資料庫、**不回傳明文給前端**（回傳遮罩如 `sk-****`）；前端只送新值。
- **設定頁存取走後端 API**（例：`GET/POST/PUT/DELETE /api/settings/llm-providers`、`PUT /api/settings/llm-active`），前端設定頁做 CRUD + 選用；風格照 `../frontend/*.md`。
- **工廠介面不變**：`get_chat_model()` 改成「從資料庫讀 active 那筆設定」來建構，而不是讀 `.env`——但對上層（service / LangGraph node）**完全一樣**（§3、§4 不動）。

### 5.2 工廠改讀資料庫（示意）

資料表用 SQLAlchemy Core（見 `database.md`），工廠改成讀「目前選用」那筆：

```python
# backend/llm/__init__.py（有前端版：從 DB 讀設定）
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from services.llm_provider_service import get_active_provider  # 讀 DB，回傳一筆設定 dict


def get_chat_model(provider_id: int | None = None) -> BaseChatModel:
    """從資料庫取使用者註冊的 provider 設定來建構（有前端版）。
    provider_id 省略時用專案目前選用（active）那筆。上層用法與 .env 版完全相同。
    """
    cfg = get_active_provider(provider_id)   # {provider, base_url, model, api_key, temperature, ...}

    if cfg["provider"] == "ollama":
        return ChatOllama(
            model=cfg["model"],
            base_url=cfg["base_url"],
            temperature=cfg.get("temperature", 0.0),
        )
    if cfg["provider"] == "openai":          # 外部 OpenAI 或本地 vLLM
        return ChatOpenAI(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",
            temperature=cfg.get("temperature", 0.0),
        )
    raise ValueError(f"未知的 provider: {cfg['provider']!r}")
```

> 建構分支（ollama / openai、vLLM 當 OpenAI）與 §3 完全相同，差別只在「設定從 DB 來、由使用者在前端註冊多筆並選用」。上層照舊 `from llm import get_chat_model`。

---

## 6. 慣例小結

- **設定來源看有沒有前端**：有前端 → 使用者在**設定頁註冊多個 provider、存資料庫、選用**（§5，細節交接手 session 設計）；無前端 → **`.env`**（§2）。
- **兩後端並存**：`ChatOllama`（本地 Ollama）＋ `ChatOpenAI`（外部 OpenAI / 本地 vLLM）。
- **vLLM 當成 OpenAI**：用 `ChatOpenAI` + 指到 vLLM 的 `base_url`（`/v1`），`api_key` 給 `"EMPTY"` 之類即可。
- **只從 `get_chat_model()` 建構**：不管設定來自 `.env` 或 DB，工廠介面與上層用法不變。
- 上層（service、LangGraph node）拿到的是統一介面，`invoke` / `stream` / `bind_tools` 通用。
