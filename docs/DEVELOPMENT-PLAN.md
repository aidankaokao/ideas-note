# ideas-note 開發計劃書

> 靈感筆記：隨時（含手機）記錄靈感，AI agent 幫忙延伸、結合、建立知識體系、問答、心智圖。
> 慣例一律照 `reference/`；本文件記錄「本專案」的決策與細節。最後更新：2026-07-25。

---

## 1. 已確認的需求決策（開工前與開發者確認）

| 問題 | 決策 |
|---|---|
| 語音輸入 | **第一版不做**（手機鍵盤內建語音輸入可頂替；之後可加 Web Speech API 或 Whisper） |
| Agent 功能 | 四模組全做：靈感延伸與引導、靈感連結與結合、知識體系與問答（RAG）、心智圖 |
| 檢索方式 | **OpenAI embedding**（向量存 `notes.embedding` JSON 欄位，Python 算 cosine） |
| 存取保護 | **帳密登入存資料庫**：bcrypt 雜湊、JWT（30 天）、預設 `admin/admin`（首啟自動種入）、管理員可在設定頁新增/管理帳號 |
| 前端風格 | Aurora Glass（極光琉璃），含 8 套可切換主題盤；手機優先（桌機 Sidebar、手機底部導覽） |
| LLM 設定 | 前端設定頁註冊多個 provider（存 DB、key 遮罩回傳），可「測試連線」，分別選用**對話**與 **embedding** 兩個 active |
| 資料庫 | SQLAlchemy Core；開發 SQLite（`backend/data/app.db`），部署換 **Neon PostgreSQL**（只改 `DATABASE_URL`＋裝 `psycopg[binary]`） |
| 部署 | 現在不出 Docker；最終 **GCP Cloud Run**，屆時另寫一步一步的部署指南放 `docs/`（用 GCP 網頁介面操作） |
| Skill | 目前無明確需求，暫不建 `backend/skills/`；之後有可重用能力再依 `skill-design.md` 抽出 |
| 套件 | 只用開源 / 免費套件（OpenAI API 為使用者自備 key 的用量計費，非套件費） |

## 1.5 v2 介面改版：靈感導師（2026-07-25，與開發者確認後實作）

把分散的功能頁整併成「**一個導師對話框做所有事**」：

- **主頁＝導師對話**：輸入框下兩鍵「記筆記」（直接存筆記）與「問答」（交給導師）。導師是 LangGraph ReAct tool-loop（`agents/mentor_agent.py`），自主調度工具：檢索/翻找筆記、建立筆記、**修改提案**（不直接改，前端出「套用」按鈕）、找相關結合、整理知識體系、生成並保存心智圖。每則回覆附 3 個可點的建議問題；工具副作用以 actions 回傳，前端渲染成卡片。
- **每日導師簡報**：每帳號每天第一次進主頁生成一次（快取在 `briefings` 表），導師主動回顧/提醒/給建議問題；LLM 未設定時給靜態 fallback（不快取）。
- **對話保存**：`chat_messages` 表，thread=`main`（主頁）/`note:<id>`（每篇筆記各自的聚焦對話），可清空。
- **靈感庫**（原靈感牆）：純翻找——搜尋＋主題篩選 chips（來自知識體系）＋分頁**每頁 5 筆**。
- **筆記詳情**：編輯＋連結＋右下懸浮導師鈕 → 聚焦對話側欄（預設快捷指令：延伸/找結合/依討論修改），套用修改提案會同步畫面。
- **心智圖頁**：只查看/下載（Markdown＋SVG）/刪除導師保存過的圖（`mindmaps` 表），不再有生成 UI。
- 舊的 `/agent/extend|connect|qa|mindmap|organize` 端點保留可用（導師工具走 service 層），但 UI 已不直接呼叫；`/chat`、`/knowledge` 路由導向新頁。
- 新表都是「新增」，`metadata.create_all` 會自動補建，**既有開發 DB 不用重建**。

### v2.1 修正（2026-07-25）

- **主頁輸入框固定底部**：主頁 main 改 `overflow-hidden`，訊息區內部捲動（`MentorChat fill`）；手機版輸入區可收合成右下懸浮鈕。
- **IME 修正**：注音等輸入法組字中按 Enter（`isComposing` / keyCode 229）不送出。
- **上下文 compact**：對話字元估算超過預算（16000 字）80% 時，自動把舊訊息（保留最近 4 則）壓縮成摘要存 `chat_summaries`（per thread），之後上下文＝摘要＋新訊息。輸入框左下「記憶 x%」可點開查看百分比與摘要（`GET /agent/mentor/context`；POST 回應也帶 `context`）。
- **資料完全依帳號隔離**：`llm_providers` 加 `user_id`、active 選用 key 改 `active_*_provider_id:<user_id>`（`llm/` 工廠與所有 LLM/embedding 呼叫都帶 user_id）；刪帳號連帶刪對話/摘要/心智圖/簡報/provider 設定。⚠️ 此變更動到既有表欄位，**開發期 DB 需重建一次**（刪 `backend/data/app.db` 重啟即可）。

### v2.2（2026-07-25）

- **串流輸出**：導師改走 `POST /agent/mentor/stream`（SSE：`token` 逐字 → `done` 帶 reply/suggestions/actions/context；錯誤以 `error` 事件回報）。後端 `stream_mentor()` 用 `graph.stream(stream_mode="messages")` 只外流 agent node 的 LLM token；前端 `api.stream()` 讀 ReadableStream 邊收邊渲染。非串流 `POST /agent/mentor` 保留。部署 nginx 記得 `proxy_buffering off`（接線文件本有此慣例）。
- **觸控裝置 Enter＝換行**：`(pointer: coarse)` 偵測，手機上送出只靠「問答」鈕；桌機維持 Enter 送出、Shift+Enter 換行。
- **知識體系流動化**：新筆記建立後背景執行緒自動 `topic_service.classify_note()`——LLM 決定歸入哪些既有主題／都不合適才開新主題／必要時微調主題名；失敗（未設 provider 等）靜默略過。尚無任何主題時不動作（先請導師 organize 一次）。全量重整（organize_topics）仍在。
- **主題心智圖**：導師新增 `get_topic_notes(topic_id)` 工具，「幫我把◯◯主題畫成心智圖」→ list_topics 找 id → get_topic_notes 取筆記 → save_mindmap。

### v2.3：畫面 session 與長期記憶分離（2026-07-25）

- **畫面＝一次 session**：MentorChat 不再載入歷史，重刷/重開瀏覽器畫面都是乾淨的；「清空畫面」只清前端 state，不打 API。
- **長期記憶＝DB**：每輪對話照樣寫入 `chat_messages`＋自動 compact；「記憶 x%」＝摘要＋近期未壓縮對話（compact 後降但不歸零，摘要即長期記憶）。記憶 dialog 顯示組成明細，並提供「清除長期記憶」鈕（DELETE /agent/mentor/history，連摘要一起刪）。
- `GET /agent/mentor/history` 端點保留但 UI 已不使用。
- **心智圖頁可直接生成（多張並存）**：範圍＝全部／某主題／自訂描述（`POST /agent/mindmap` 新增 `query`，走語意檢索取材；生成即存 `mindmaps` 表並回 `id`）。導師對話生成的路徑照舊。
- **心智圖管理**：`mindmaps` 加 `topic_id`/`query` 記住生成範圍（用 `run_light_migrations()` 的 ALTER TABLE 輕量遷移補欄位，開發庫不必重建）；`POST /mindmaps/{id}/regenerate` 依原範圍重新取材重畫（主題已消失→退回用標題語意檢索）、`PUT /mindmaps/{id}` 手動編輯標題與 markdown。前端：chips 超過 12 張收合成「+N 更多」、選中卡片有 重新生成/編輯/下載/刪除。

## 2. 架構總覽

```
backend/  Python 3.11 + FastAPI（python api.py，port 8000，路徑前綴 /api）
├── api.py            進入點；lifespan：建 data/、metadata.create_all、seed admin/admin
├── config.py         pydantic-settings（DATABASE_URL、JWT_SECRET…）
├── db/               engine.py（SQLite/PG 切換）、tables.py（Core Table）
├── routers/          auth / users / notes / topics / providers(settings) / agent（+deps.py JWT 依賴）
├── services/         auth(bcrypt+JWT) / user / note / provider / embedding(cosine) / topic
├── llm/              get_chat_model() / get_embedding_model() 工廠：讀 DB 選用 provider
└── agents/               idea_agent.py（五個功能 graph）＋ mentor_agent.py（導師 ReAct tool-loop＋每日簡報）

frontend/ Vite + React 18 + TS + Tailwind（Aurora Glass），npm run dev（5173，/api proxy→8000）
├── src/lib/          api.ts（薄 client＋JWT header＋401 導回登入）、themes.ts（8 主題盤）、types.ts
├── src/stores/       auth（zustand persist）、pageHeader、ui（sidebar 折疊）
├── src/components/   GlassBackground、ProgressHint、ui/*（button/card/input/…）、layout/*（Sidebar 可拖曳折疊、Header、MobileNav）
├── src/components/MentorChat.tsx  共用導師對話（主頁與筆記側欄）：簡報卡、動作卡片、建議 chips、記筆記/問答雙鍵
└── src/pages/        Login / Assistant(主頁導師) / Library(靈感庫:搜尋+主題篩選+每頁5筆) /
                      NoteDetail(編輯+連結+聚焦對話側欄) / MindMap(查看/下載/刪除) / Settings
```

## 3. 資料表（backend/db/tables.py）

- `users`：id, username(unique), password_hash(bcrypt), is_admin, created_at
- `notes`：id, user_id, title, content, source(manual/agent-extend/qa-extract), embedding(JSON), created_at, updated_at
- `note_links`：id, user_id, from_note_id, to_note_id, reason（雙向去重）
- `topics` / `note_topics`：AI「整理」整批重建（replace）
- `llm_providers`：name, provider(openai/ollama), base_url, model, api_key, temperature
- `app_settings`：key-value（active_chat_provider_id / active_embedding_provider_id）
- `chat_messages`：導師對話（thread=main / note:<id>；assistant 的 payload 存 suggestions+actions）
- `mindmaps`：導師保存的心智圖（title, markdown）
- `briefings`：每日簡報快取（user_id+date 複合主鍵，payload JSON）

## 4. API 一覽（全部 `/api` 前綴；除 login/health 外皆需 Bearer JWT）

- `POST /auth/login`、`GET /auth/me`、`PUT /auth/password`
- `GET|POST /users`、`PUT|DELETE /users/{id}`（管理員；保護最後一個管理員、不能刪自己）
- `GET|POST /notes`、`GET|PUT|DELETE /notes/{id}`、`GET /notes/{id}/related`、
  `GET|POST /notes/{id}/links`、`DELETE /notes/links/{link_id}`
  - `POST /notes` 支援 `link_from_note_id`（AI 結果存新靈感時自動建連結）；title 空白時取內容第一行前 30 字
- `GET /topics`
- `GET|POST /settings/llm-providers`、`PUT|DELETE /settings/llm-providers/{id}`、
  `POST /settings/llm-providers/test`（列模型清單驗證；編輯時可沿用已存 key）、`GET|PUT /settings/llm-active`
- `POST /agent/extend|connect|qa|mindmap|organize`（ValueError→400 給使用者看；LLM 錯誤→502；v2 後 UI 不直接用，保留）
- `POST /agent/mentor`（{message, note_id?} → {reply, suggestions, actions}）、
  `GET|DELETE /agent/mentor/history?note_id=`、`GET /agent/mentor/briefing`
- `GET /mindmaps`、`DELETE /mindmaps/{id}`

## 5. Agent 設計（backend/agents/idea_agent.py，LangGraph）

| graph | 流程 | 輸出 result |
|---|---|---|
| extend | load_note → extend | extensions[]（可存回新靈感＋自動連結）、questions[]、next_steps[] |
| connect | load_note → find_related →（條件分支）combine / empty | summary、combinations[]（建連結/存靈感）、related[] |
| qa | retrieve(embedding top8) → answer | answer(markdown, 引用[#id])、sparks[]（一鍵萃取成筆記）、sources[] |
| mindmap | gather(全部或指定 topic) → mindmap | markdown（前端 markmap 渲染）、note_count |
| organize | gather → cluster → save(replace_topics) | topics[]（整批重建知識體系） |

- LLM 統一 `_ask_json()`：系統提示要求單一 JSON、繁中；`_parse_json` 容錯（去 code fence、抓大括號）。
- 向量化 best-effort：筆記存檔即嘗試 embed，失敗不擋存檔（`try_embed_note`）；檢索時遇缺再補算。

## 6. 執行方式（開發期）

```bash
# 後端（終端 1）
cd backend
python3.11 -m venv .venv && source .venv/bin/activate   # 首次
pip install -r requirements.txt                          # 首次
cp .env.example .env                                     # 首次
python api.py                                            # http://localhost:8000

# 前端（終端 2）
cd frontend
npm install                                              # 首次
npm run dev                                              # http://localhost:5173
```

首次使用：以 admin/admin 登入 → 設定頁改密碼 → 註冊 LLM provider（對話用如 gpt-4o-mini；embedding 用如 text-embedding-3-small）→ 測試連線 → 兩個下拉分別選用。

## 7. 部署（2026-07-25 已就緒）

- **指南**：`docs/DEPLOY-CLOUD-RUN.md`（GCP 介面一步一步：GitHub 持續部署 ＋ Neon 免費方案）。
- **方案**：單一容器（根目錄 `Dockerfile` 多階段：node build 前端 → 靜態檔放 `backend/static/` 由 FastAPI 伺服＋SPA fallback）；不用 nginx、不用 APP_ROUTE（掛根路徑）——與 reference deploy 流程的既定偏差。
- **程式配合**：`api.py` 讀 `PORT` env（Cloud Run 注入 8080、本機仍 8000）＋伺服 static；`requirements.txt` 已含 `psycopg[binary]`；env：`DATABASE_URL`（Neon `postgresql+psycopg://…?sslmode=require`）、`JWT_SECRET`。
- Cloud Run 設定重點：port 8080、記憶體 1GiB、逾時 600s（SSE）、執行個體 0~1、允許未驗證叫用（App 內建帳密）。
- 待辦（之後）：正式環境改表結構時導入 Alembic（`database.md` §7）。
- **上線後修正（2026-07-25）**：SPA catch-all（`GET /{full_path:path}`）原本註冊在 include_router 之前，把所有 GET `/api/*` 攔走回 index.html（前端報「Unexpected token '<' … not valid JSON」）。已移到**所有 API 路由之後**並加註警告——之後動 `api.py` 路由順序時務必維持：`/api` 路由在前、static/catch-all 最後。

## 8. 未來可能的擴充（已討論、未排程）

- 語音輸入（Web Speech API 免費；或錄音上傳 Whisper）
- 問答/延伸改 SSE 串流逐字輸出（nginx 已留 `proxy_buffering off` 慣例）
- 筆記量大後：embedding 檢索改 pgvector（Neon 支援）
