# 開發模板包（Design & Dev Template）

> 一句話：這是一包**「開新專案用的起手模板 + 開發慣例」**。把它當新專案的起點，照下面步驟做完，
> 新的 Claude Code session 只要讀 `reference/` 就能照你慣用的**框架、風格、部署方式**開發，
> 你只需要**講需求**，不用每次重打技術棧與注意事項。

---

## 這一包裡有什麼

```
.
├── README.md                         ← 你正在看的這份（怎麼用這一包）
├── CLAUDE.md                         這一包的總覽索引（瀏覽用；開新專案時會被 bootstrap 版取代）
│
├── new-project-root-CLAUDE.md        ★ 複製到新專案根目錄、改名為 CLAUDE.md（AI 開發入口）
├── new-project-kickoff-prompt.md     ★ 開新 session 時，貼進第一則訊息的起手 prompt
├── project-requirements-TEMPLATE.md  ★ 複製成 reference/PROJECT-REQUIREMENTS.md 後填寫需求
│
├── docker-compose.yaml               部署起手檔（放在專案根，與 backend/ frontend/ 同層）
├── Dockerfile.backend
├── Dockerfile.frontend
├── build.sh                          自己 build image（命名 / route 走 .env）
├── .env.example                      → cp 成 .env 改值（IMAGE_PREFIX / APP_ROUTE / PORT …）
│
└── reference/                        開發慣例 + 起手檔（新 session 讀這裡，保留在專案內）
    ├── backend/                      FastAPI / LangGraph / LLM / DB / SKILL 慣例 + requirements.txt、.env.example
    ├── frontend/                     三種視覺風格 + 前後端接線 + vite/tsconfig/package.json/nginx 等起手檔
    └── deploy/                       deploy-guide.md（部署完整說明）+ .env.example
```

> `★` = 開新專案時需要你動手的檔案。其餘 `reference/` 與部署起手檔照抄即可。

---

## 快速開始：開一個新專案（6 步）

### 0. 放到新專案資料夾
把這一整包（或其內容）放進你的新專案資料夾，讓它成為專案根目錄。

### 1. 設定 AI 開發入口
把 `new-project-root-CLAUDE.md` **複製一份、改名為 `CLAUDE.md`**（取代這包原本的索引 `CLAUDE.md`）。
Claude Code 啟動時會自動讀根目錄 `CLAUDE.md`，於是每個新 session 一開就會照它的指示去讀 `reference/`。

```bash
cp new-project-root-CLAUDE.md CLAUDE.md
```

### 2. 填寫專案需求
把需求範本複製成 `reference/PROJECT-REQUIREMENTS.md` 並填寫（勾選式：前端風格、有無前端、要不要 agent / DB / LLM、部署命名…）。

```bash
cp project-requirements-TEMPLATE.md reference/PROJECT-REQUIREMENTS.md
# 然後打開編輯，把需求勾一勾、填一填
```

### 3. 設定部署 .env
複製 `.env.example` 成 `.env`，改成本專案的值（**只改這一處，compose 與 build.sh 都吃它**）：

```bash
cp .env.example .env
# 重點：IMAGE_PREFIX（=專案名）、APP_ROUTE（路由名）、FRONTEND_PORT（對外埠）
```

### 4. 開 session、貼起手 prompt
在專案根目錄開一個新的 Claude Code session，把 `new-project-kickoff-prompt.md` 的內容**貼進第一則訊息**。

### 5. 讓 Claude 依需求 + 慣例開發
Claude 會：讀 `CLAUDE.md` + `reference/PROJECT-REQUIREMENTS.md` + `reference/` 慣例 → 先跟你**確認需求沒寫清楚的項目** → 給你一份建置計畫 → 開始幫你生 `backend/`、`frontend/`（從 `reference/` 複製起手檔、貼上選定風格的樣式）。

### 6. 部署（需要時）
```bash
# 首次：建外部網路（名稱＝ .env 的 NETWORK_NAME）
set -a; . ./.env; set +a
docker network create "$NETWORK_NAME"     # 已存在就跳過

./build.sh                                # 自己 build image
docker-compose up -d                      # 起服務（舊命令）
```
- **內網**訪問：`http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/`
- **外網**（團隊 nginx 綁 DNS）：`https://<DNS>/<APP_ROUTE>/`

---

## 完成後：專案根會長這樣

```
新專案根/
├── CLAUDE.md                 ← 由 new-project-root-CLAUDE.md 改名
├── docker-compose.yaml / Dockerfile.* / build.sh / .env
├── backend/                  ← Claude 依 reference/backend 生成（api.py、requirements.txt、.env、data/ …）
├── frontend/                 ← Claude 依選定風格 + reference/frontend 生成（src/、config、nginx.conf.template …）
└── reference/                ← 保留：未來 session 的開發慣例來源
```

> 收尾可刪掉的「模板腳手架」：`README.md`、原本的套件 `CLAUDE.md` 索引、`new-project-root-CLAUDE.md`（已改名）、`new-project-kickoff-prompt.md`、`project-requirements-TEMPLATE.md`。
> **`reference/` 要保留**（之後的 session 仍會讀它）。

---

## 檔案用途對照表

| 檔案 / 資料夾 | 用途 | 開新專案時 |
|---|---|---|
| `new-project-root-CLAUDE.md` | AI 開發入口（指示讀需求 + reference） | 複製→改名 `CLAUDE.md` |
| `project-requirements-TEMPLATE.md` | 需求填寫表單 | 複製→ `reference/PROJECT-REQUIREMENTS.md` 填寫 |
| `new-project-kickoff-prompt.md` | 新 session 的起手 prompt | 貼進第一則訊息 |
| `.env.example` | 部署層變數範本 | `cp` 成 `.env` 改值 |
| `docker-compose.yaml` / `Dockerfile.*` / `build.sh` | 部署起手檔 | 照抄（放專案根）|
| `reference/backend/` | 後端慣例（FastAPI / LangGraph / LLM / DB / SKILL）+ 起手檔 | 保留、開發時複製起手檔 |
| `reference/frontend/` | 三種前端風格 + 前後端接線 + 前端 config 起手檔 | 保留、開發時複製起手檔 |
| `reference/deploy/` | 部署完整說明 `deploy-guide.md` | 保留（查閱用）|

---

## 三種前端風格速選

在 `reference/frontend/` 裡三選一（細節見各檔）：

| 風格 | 關鍵字 | 典型畫面 |
|---|---|---|
| **Formal**（`frontend-style-formal.md`）| 密集、專業、對內 | admin 後台、報表儀表板 |
| **Glass Wave**（`frontend-style-glass-wave.md`）| 清爽、質感、單色藍 | 有體面感的產品主介面 |
| **Aurora Glass**（`frontend-style-aurora-glass.md`）| 品牌漸層、吸睛、可換主題 | AI 產品、landing、對外前台 |

> 判準：資訊越密、越對內 → **Formal**；越要品牌氛圍、越對外 → **Aurora Glass**；中間想清爽有質感 → **Glass Wave**。

---

## 小提醒

- **`.env` 要和 `build.sh` / `docker-compose.yaml` 同層**（專案根），因為它們讀同目錄的 `.env`。
- **改了 `APP_ROUTE` 或 `IMAGE_PREFIX` 要重跑 `./build.sh`**（route 在 build 時烤進前端 image；tag 由命名決定）。
- **`backend/` 與 `frontend/` 是開發時才生出來的**；部署檔（Dockerfile / compose）預期它們在專案根、與部署檔同層（build context = 專案根）。
- 兩種 `.env` 分工：根目錄 `.env` = 部署層（port / 命名 / route，compose 讀）；`backend/.env` = 應用層（DB / LLM，程式讀）。
