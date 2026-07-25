# 後端開發慣例（Python + FastAPI · 可攜式）

> 這份文件把我後端專案的**技術棧與開發慣例**抽離成一份自足規範，
> 目的是：**新的 Claude Code session 只看這一份（＋同資料夾的其他 backend 文件），就能在全新專案裡照我習慣的方式起後端。**
> 這是 backend 資料夾的**入口與總覽**；各主題細節分別在對應文件。

---

## 0. 一句話總結

**Python 3.11 + FastAPI**，API 程式自帶 `uvicorn.run`（port 8000），最終用 **Docker 容器打包對外**。
AI agent 用 **LangGraph**；LLM 走 **ChatOllama（本地）/ ChatOpenAI（外部或本地 vLLM）**；資料庫用 **SQLAlchemy Core**（初期 SQLite、之後無縫換 PostgreSQL）；skill 用 **`SKILL.md`** 設計。

---

## 1. 執行環境

- **Python 版本固定 3.11**（不要用 3.12+ 的語法假設；容器基底一律 `python:3.11-slim`）。
- 依賴用 `requirements.txt` 管理（容器 `pip install --no-cache-dir -r requirements.txt`）。
- 本機開發可用 `venv`：
  ```bash
  python3.11 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```

---

## 2. 各主題文件導覽（新 session 依需求選讀）

| 需求 | 讀這份 |
|---|---|
| 起 FastAPI 服務、`uvicorn.run` 慣例、專案結構 | **本文件 §3~§5** |
| 開發 AI agent（LangGraph） | `langgraph-agent.md` |
| 呼叫 LLM（本地 Ollama / 外部 OpenAI / 本地 vLLM） | `llm-integration.md` |
| 資料庫（SQLite → PostgreSQL，SQLAlchemy Core） | `database.md` |
| 設計 skill（`SKILL.md`） | `skill-design.md` |
| 打包部署（Docker Compose） | `../deploy/deploy-guide.md` |

---

## 3. FastAPI 服務慣例（重點！）

**API 進入點檔名用 `api.py`。** 一律在檔案底部 `if __name__ == "__main__"` 內直接 `uvicorn.run`，port 固定 `8000`、host `0.0.0.0`（容器內對外）。這樣「直接 `python api.py` 就能跑」，且容器 `CMD ["python", "api.py"]` 一致。

```python
# backend/api.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動：初始化資料庫連線 / 預熱模型等（見 database.md）
    yield
    # 關閉：釋放資源


app = FastAPI(title="my-service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 開發期放寬；上線改成實際前端來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── 路由掛載（大專案用 APIRouter 分檔，見 §4）──
# from routers import items
# app.include_router(items.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    # host 0.0.0.0 讓容器對外可達；port 8000 為容器內埠，
    # 對外埠由 docker-compose 的 .env 映射（見 deploy-guide.md）。
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

要點：
- **host `0.0.0.0`、port `8000` 寫死在程式內**（容器內埠固定），對外埠交給 docker-compose `.env` 映射，不在程式裡處理。
- 開發熱重載時才用 `uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)`（傳字串路徑）；容器內跑成品**不開 reload**。
- 所有 API 路徑統一前綴 `/api`（前端 nginx 反代/子路徑部署較好對接）。

---

## 4. 建議專案結構

```
backend/
├── api.py                 # 進入點：FastAPI app + uvicorn.run(__main__)
├── requirements.txt
├── .env                   # 本機/容器環境變數（不進版控）
├── config.py              # 讀 env → 設定物件（pydantic-settings）
├── routers/               # APIRouter 分檔
│   ├── __init__.py
│   └── items.py
├── db/                    # 資料庫（見 database.md）
│   ├── engine.py          # SQLAlchemy Engine / 連線字串
│   └── tables.py          # Core Table 定義（MetaData）
├── services/              # 商業邏輯（與 FastAPI 解耦，好測試）
├── agents/                # LangGraph agent（見 langgraph-agent.md）
├── llm/                   # LLM 建構（見 llm-integration.md）
├── skills/                # 各 skill 目錄，每個含 SKILL.md（見 skill-design.md）
└── data/                  # SQLite 檔 / 執行期產物（容器掛 volume）
```

- **路由薄、service 厚**：`routers/` 只做請求解析與回應；邏輯放 `services/`，方便單元測試與被 agent 重用。
- `data/` 在容器內掛 volume（見 deploy），SQLite 檔與產出放這。

---

## 5. 設定與環境變數（`config.py`）

用 `pydantic-settings` 讀 `.env`，集中成一個設定物件；**程式各處只 import 這個物件，不散落 `os.getenv`**。

```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 資料庫（見 database.md）：初期 sqlite，之後換 postgres 只改這行
    database_url: str = "sqlite:///./data/app.db"

    # LLM（見 llm-integration.md）
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""

    app_env: str = "dev"           # dev / prod


settings = Settings()
```

`.env` 範例（實際值不進版控，只留 `.env.example`）：

```dotenv
DATABASE_URL=sqlite:///./data/app.db
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
APP_ENV=dev
```

> 注意區分兩種 env：**應用層 env**（上面這些，backend 程式讀）與 **部署層 env**（容器對外埠、labels，docker-compose 讀，見 deploy-guide.md）。兩者可放不同 `.env`。

---

## 6. requirements.txt 起手式

依實際用到的模組增減；常見基底：

```txt
fastapi>=0.110
uvicorn[standard]>=0.29
pydantic>=2.6
pydantic-settings>=2.2
sqlalchemy>=2.0            # Core 寫法，見 database.md
# ── AI / LLM（需要才加）──
langgraph>=0.2            # 見 langgraph-agent.md
langchain-core>=0.3
langchain-ollama>=0.2     # ChatOllama（本地）
langchain-openai>=0.2     # ChatOpenAI（外部 / 本地 vLLM）
```

---

## 7. 給新 session 的「照做」清單

1. 確認 Python 3.11；建 `backend/` 用 §4 結構。
2. 寫 `api.py`：FastAPI app + `/api/health` + 底部 `if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)`（§3）。
3. 建 `config.py`（`pydantic-settings`）＋ `.env` / `.env.example`（§5）。
4. 依需求讀對應主題文件：agent → `langgraph-agent.md`、LLM → `llm-integration.md`、DB → `database.md`、skill → `skill-design.md`。
5. 打包時照 `../deploy/deploy-guide.md`：容器 `CMD ["python", "api.py"]`、對外埠走 compose `.env`。

> 一句判準：**「`python api.py` 直接起服務、port 8000、邏輯在 service 層、之後 docker-compose up -d 就能上」** 就對了。
