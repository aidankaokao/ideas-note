# 專案需求說明（開發者填寫）

> **用法**：開新專案時複製這份到 `reference/PROJECT-REQUIREMENTS.md` 並填寫。
> 新的 Claude Code session 會先讀根目錄 `CLAUDE.md` + 這份需求 + `reference/` 慣例，再開工。
> 勾選用 `[x]`；不確定的留白，session 會在開工前一次問你。

---

## 1. 專案基本

- **專案名稱**：ideas-note
- **APP_ROUTE（路由名稱，內外網共用；見 deploy-guide 路由機制）**：ideas-note
- **一句話目標**：記錄靈感的筆記，介面需要支持手機版模式，讓我可以隨時記錄靈感，並通過ai agent幫我整理靈感，包含與其他靈感的結合、靈感的延伸等。會需要用gcp的cloud run部署。

## 2. 前端

- [x] 需要前端
- [ ] 不需要前端（純後端 / API / CLI）
- 若需要，**視覺風格三選一**（見 `reference/frontend/frontend-style-*.md`）：
  - [ ] Formal（乾淨後台 SaaS）
  - [ ] Glass Wave（淡藍紫玻璃波）
  - [x] Aurora Glass（極光琉璃，可切主題盤）
- **主要頁面 / 功能**：隨時記錄一篇靈感筆記，需支持手機模式，未來部署在cloud run後我可以隨時通過手機紀錄靈感。

## 3. 後端

- [x] 需要後端 API（FastAPI，見 `reference/backend/backend-conventions.md`）
- **主要 API / 功能**：除了支援前端需求外，還包括手機端可以操作紀錄靈感筆記的功能，例如語音輸入。

## 4. AI Agent

- [x] 需要 AI agent（LangGraph，見 `reference/backend/langgraph-agent.md`）
- **流程 / 說明**：ai agent通過將記錄的靈感做延伸、引導、與其他靈感結合，或是你認為有其他方式可以擴展我的靈感，我的發想可能會有知識體系建立、我的知識體系的問答（包含問答中可以再萃取出靈感）、形成心智圖等等，你可以幫我設計看看，這套靈感筆記是要對我有幫助，不僅僅只是紀錄而已。

## 5. LLM

- [x] 需要用到 LLM（見 `reference/backend/llm-integration.md`）
- provider：[ ] 本地 Ollama　[x] 外部 OpenAI　[ ] 本地 vLLM
- 設定來源：[x] 前端設定頁註冊多個（有前端建議）　[ ] `.env`（無前端）
- **模型**：前端設定頁面註冊LLM provider，並在註冊前有按鈕可以測試連線。

## 6. 資料庫

- [x] 需要資料庫（SQLAlchemy Core，見 `reference/backend/database.md`）
- 初期 [x] SQLite　→ 之後 [x] PostgreSQL
- **主要資料表 / 實體**：部署時postgres會以neon方式進行，初期開發可先以sqlite。

## 7. Skill

- [x] 需要設計 skill（`SKILL.md`，見 `reference/backend/skill-design.md`）
- **說明**：若有需求。

## 8. 部署

- [ ] 現在就要 Docker 部署（見 `reference/deploy/deploy-guide.md`）
- **IMAGE_PREFIX**（image 命名前綴，通常＝專案名）：ideas-note
- 前端對外埠 **FRONTEND_PORT**：在.env進行設定
- 內網訪問：`http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/`
- 之後綁 DNS（團隊 nginx）：`https://<DNS>/<APP_ROUTE>/`

## 9. 其他需求 / 注意事項（自由填寫）

- 只能使用開源或免費的套件，不可使用商業或付費套件。
- 你不可以幫我執行程式，只能修改程式，若要執行請直接給我命令，我自己執行。
- 每次修改完程式請自動更新CLAUDE.md。
- 盡可能保持CLAUDE.md簡潔(盡可能不要超過100行，嚴禁超過300行)，若有關於專案細節請另外填寫開發計劃書或其他相關文件，並在CLAUDE.md中提示閱讀即可。
- 此專案部署最後會在cloud run進行部署，postgres會以neon免費方案為主，請在最後部署階段幫我寫一份部署具體步驟指南，我習慣用gcp的介面操作，需很具體的一步一步跟我說，可以把部署指南寫在docs資料夾內。
