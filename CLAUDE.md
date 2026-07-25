<!--
  這是「新專案根目錄」用的 CLAUDE.md 範本。
  用法：把 backend/ frontend/ deploy/ 放進新專案的 reference/ 後，
  把這份檔複製到【新專案根目錄】並改名為 CLAUDE.md。
  Claude Code 啟動時會自動讀取根目錄 CLAUDE.md，於是每個新 session
  一開就會照下面指示去讀 reference/ 裡的慣例，你只要講需求即可。
-->

# 專案開發指引（本專案的開發慣例入口）

## 本專案現況（2026-07-25 已開工）

- **ideas-note 靈感筆記**：Aurora Glass 前端（手機優先）＋ FastAPI 後端 ＋ LangGraph ＋ 前端設定頁註冊 LLM provider ＋ SQLite（部署換 Neon PG）。
- **v2 介面＝「靈感導師」**：主頁單一對話框（記筆記/問答雙鍵），導師 agent（ReAct tool-loop）自主調度延伸/結合/問答/整理/心智圖/修改提案等工具；靈感庫＝翻找（搜尋+主題篩選+每頁5筆）；心智圖頁只查看/下載。對話有自動 compact（超 80% 壓縮成摘要，UI 可看「記憶 %」）；**所有資料（含 LLM 設定）完全依帳號隔離**。
- **需求確認、架構、資料表、API、agent 設計、執行方式、部署待辦**：一律見 **`docs/DEVELOPMENT-PLAN.md`**（開發計劃書），下方「開工前確認」各題的答案也記在那裡，不必再問。
- 結構：`backend/`（`python api.py`，port 8000）＋ `frontend/`（`npm run dev`，port 5173）。
- 登入：帳密存 DB（bcrypt＋JWT），首啟自動種 `admin/admin`；管理員可在設定頁管理帳號。
- 部署（已就緒）：GCP Cloud Run 單一容器（根目錄 `Dockerfile`）＋ Neon PG；操作步驟見 `docs/DEPLOY-CLOUD-RUN.md`。
- 規則：只用開源/免費套件；**不執行程式**（命令給開發者自己跑）；每次改完程式更新本檔與計劃書，本檔保持精簡（<100 行）。

> 我把常用的開發框架與注意事項放在 **`reference/`** 資料夾（`reference/backend`、`reference/frontend`、`reference/deploy`）。
> **動工前務必依序讀：**
> 1. **`reference/PROJECT-REQUIREMENTS.md`** —— 本專案的需求（我已填寫）。
> 2. 下方「文件地圖」中對應的細節文件（都在 `reference/`）。
>
> **一律照 `reference/` 的慣例做，不要自行發明架構或風格；需求以 `PROJECT-REQUIREMENTS.md` 為準。**

---

## ⚠️ 開始寫任何程式前，先跟我確認這幾題

需求給你後，**先問清楚以下幾點再動工**（這些會決定你要讀哪些 reference 文件、怎麼搭）：

1. **要不要前端？**
   - 要 → 用哪種視覺風格？**Formal（乾淨後台）/ Glass Wave（玻璃波）/ Aurora Glass（極光琉璃）** 三選一（見 `reference/frontend/`）。
   - 要 → LLM provider 設定就走「**前端設定頁註冊多個**」（見 `reference/backend/llm-integration.md` §5）。
   - 不要（純後端 / CLI / 服務）→ LLM / 設定走 **`.env`**（同文件 §2）。
2. **要不要 AI agent？** 要 → 用 LangGraph（`reference/backend/langgraph-agent.md`）。
3. **要不要用到 LLM？** 要 → `ChatOllama`（本地 Ollama）/ `ChatOpenAI`（外部 OpenAI 或本地 vLLM）（`reference/backend/llm-integration.md`）。
4. **要不要資料庫？** 要 → SQLAlchemy Core，初期 SQLite、之後換 PostgreSQL（`reference/backend/database.md`）。
5. **要不要現在就出 Docker 部署？** 要 → 照 `reference/deploy/deploy-guide.md`。

> 我沒特別講的部分，一律以 `reference/` 文件的慣例為預設，不要另立一套。

---

## 文件地圖（都在 `reference/`）

| 面向 | 文件 |
|---|---|
| 前端風格（三選一）| `reference/frontend/frontend-style-formal.md`、`…-glass-wave.md`、`…-aurora-glass.md` |
| 前後端接線（dev proxy / nginx / API client）| `reference/frontend/frontend-backend-integration.md` |
| 後端入口 / FastAPI | `reference/backend/backend-conventions.md` |
| AI Agent（LangGraph）| `reference/backend/langgraph-agent.md` |
| LLM 串接 | `reference/backend/llm-integration.md` |
| 資料庫 | `reference/backend/database.md` |
| Skill 設計 | `reference/backend/skill-design.md` |
| 部署（Docker Compose）| `reference/deploy/deploy-guide.md` |
| 起手檔範本 | `reference/` 各資料夾內的 `*.example` / `package.json` / `vite.config.ts` / `requirements.txt` / `nginx.conf` 等 |

---

## 建置順序（釐清完需求後）

1. **搭骨架**：依 §上方回答，從 `reference/` 各資料夾複製 starter 起手檔（`requirements.txt`、`package.json`、`vite.config.ts`、`tsconfig*.json`、`postcss.config.js`、`nginx.conf`、`.env.example`）到專案對應位置。
2. **後端**：照 `backend-conventions.md` 起 `api.py`（`uvicorn.run`，port 8000）＋ 依需求加 agent / LLM / DB。
3. **前端**：照選定風格文件貼 `index.css` / `tailwind.config` / `ui` 元件；接線照 `frontend-backend-integration.md`（前端一律呼叫同源 `/api/...`）。
4. **部署**（需要時）：照 `deploy-guide.md`，`build.sh` 自己 build image、`docker-compose up -d`。
