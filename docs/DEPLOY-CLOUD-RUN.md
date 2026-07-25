# ideas-note 部署指南：GCP Cloud Run ＋ Neon PostgreSQL

> 目標：把靈感筆記部署到 Cloud Run，拿到一個 `https://…run.app` 網址，手機隨時可用。
> 資料庫用 Neon 免費方案。全程以 **GCP 網頁介面**操作，照順序做即可。
> 預估時間：第一次約 40–60 分鐘。

## 部署架構（先看懂再動手）

- **單一容器**：`Dockerfile`（專案根目錄）先把前端 build 成靜態檔，塞進 FastAPI 一起跑——Cloud Run 只需要一個服務，前端網頁與 `/api` 同源，免 CORS、免 nginx。
  （這與 `reference/deploy` 的 docker-compose＋nginx 流程不同，是 Cloud Run 階段的既定做法；`APP_ROUTE` 子路徑機制也不使用，直接掛在網域根路徑。）
- **資料庫**：Neon（免費雲端 PostgreSQL）。程式不用改，只要設 `DATABASE_URL` 環境變數；資料表會在服務第一次啟動時自動建立，並種入預設帳號 admin/admin。
- **部署方式**：程式推上 GitHub → Cloud Run 連結該 repo 持續部署 → 之後每次 `git push` 自動重建上線。

---

## 步驟 1：把專案推上 GitHub

1. 到 https://github.com → 右上「＋」→ **New repository**。
   - Repository name：`ideas-note`
   - 選 **Private**（程式裡沒有金鑰，但專案私有比較安心）
   - 其他都不勾，按 **Create repository**。
2. 在你的專案根目錄（`ideas-note/`）執行：

```bash
git init
git add .
git commit -m "ideas-note: initial"
git branch -M main
git remote add origin https://github.com/<你的GitHub帳號>/ideas-note.git
git push -u origin main
```

> `.gitignore` 已排除 `.env`、`backend/data/`、`node_modules/` 等，不會把本機資料推上去。

---

## 步驟 2：建立 Neon 資料庫（免費）

1. 到 https://neon.tech → **Sign up**（可直接用 Google 帳號）。
2. 建立專案：Project name 填 `ideas-note`；Region 選 **AWS Asia Pacific (Singapore)**（離台灣近）；Postgres 版本用預設 → **Create**。
3. 建好後畫面會顯示 **Connection string**（也可在 Dashboard 的「Connect」按鈕找到），長得像：

```
postgresql://neondb_owner:npg_xxxx@ep-xxxx-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

4. **改一個地方**：把開頭的 `postgresql://` 改成 **`postgresql+psycopg://`**（本專案用 psycopg3 驅動），其餘原封不動。改完像這樣，**先存到記事本**，等下要貼進 Cloud Run：

```
postgresql+psycopg://neondb_owner:npg_xxxx@ep-xxxx-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> 如果字串尾端還有 `&channel_binding=require` 之類的參數，保留即可。

---

## 步驟 3：準備 GCP 專案

1. 到 https://console.cloud.google.com → 登入 Google 帳號。
2. 頂端專案下拉 → **新增專案** → 名稱 `ideas-note` → **建立**，建好後切換到這個專案。
3. 首次使用需啟用計費帳戶（會要求綁信用卡）：左上 ≡ 選單 → **帳單** → 照指示建立。
   - 個人低流量使用大多落在 Cloud Run 免費額度內，實際費用趨近 0；後面步驟也會把「最大執行個體」設為 1 防爆量。
   - 建議順手設預算警報：**帳單 → 預算與快訊 → 建立預算**，金額設 US$5，超過會寄信提醒。

---

## 步驟 4：建立 Cloud Run 服務（連 GitHub 持續部署）

1. 左上 ≡ 選單 → **Cloud Run**（第一次會提示啟用 API，按啟用）。
2. 按 **建立服務**。
3. 選 **「透過原始碼存放區持續部署」**（Continuously deploy from a repository）→ 按 **使用 Cloud Build 設定**：
   1. Repository provider 選 **GitHub** → 按 **驗證**，登入 GitHub 並授權 Google Cloud Build（第一次會跳出安裝 Cloud Build GitHub App，選你的帳號、授權 `ideas-note` 這個 repo）。
   2. 存放區選 `<你的帳號>/ideas-note` → **下一步**。
   3. 分支填 `^main$`。
   4. Build 類型選 **Dockerfile**，來源位置填 `/Dockerfile` → **儲存**。
4. 回到服務設定頁，逐項填：
   - **服務名稱**：`ideas-note`
   - **地區**：`asia-east1（彰化）`
   - **驗證**：選 **「允許未經驗證的叫用」**（App 自己有帳密登入保護）
   - **帳單方式 / CPU 配置**：維持預設（僅在處理要求時計費）
   - **執行個體數量下限**：`0`（沒人用就不收錢；代價是冷啟動見下方說明）
5. 展開最下方 **「容器、磁碟區、網路、安全性」**：
   - **容器通訊埠**：`8080`（預設即是；程式會自動讀 Cloud Run 注入的 PORT）
   - **記憶體**：`1 GiB`（LangChain 相依較肥，512Mi 可能不夠）
   - **CPU**：`1`
   - **要求逾時**：`600` 秒（導師串流回覆較長時不被切斷）
   - **執行個體數量上限**：`1`（個人使用夠了，也防止費用暴衝）
   - 切到 **「變數與密鑰」** 分頁，新增兩個環境變數：
     | 名稱 | 值 |
     |---|---|
     | `DATABASE_URL` | 步驟 2 存下來的 `postgresql+psycopg://…` 整串 |
     | `JWT_SECRET` | 一串長隨機字元（在終端跑 `openssl rand -hex 32` 產生後貼上） |
6. 按 **建立**。Cloud Build 會開始抓 GitHub 程式碼、照 `Dockerfile` 建 image（第一次約 5–10 分鐘），完成後自動部署。
7. 部署成功後，服務頁面上方會顯示網址：`https://ideas-note-xxxxxxxx.asia-east1.run.app` ← 就是你的正式站，手機加到主畫面即可當 App 用。

---

## 步驟 5：首次上線設定

1. 打開網址 → 用 **admin / admin** 登入。
2. **馬上到「設定」改密碼**（網址是公開的，這步不能省）。
3. 設定頁註冊 LLM provider（對話 `gpt-4o-mini`、embedding `text-embedding-3-small`）→ 測試連線 → 兩個下拉選用。
4. 記一則靈感、跟導師講句話，確認一切正常。

> 資料表在第一次啟動時已自動建立在 Neon（`metadata.create_all`）。本機 SQLite 的測試資料不會帶上去，正式站是全新開始。

---

## 之後怎麼更新版本

改完程式後：

```bash
git add .
git commit -m "說明這次改了什麼"
git push
```

推上 `main` 後 Cloud Build 會自動重建並部署（Cloud Run 服務頁的「修訂版本」分頁可看進度），約 5–10 分鐘生效，資料都在 Neon 不受影響。

---

## 疑難排解

| 症狀 | 怎麼查 / 怎麼解 |
|---|---|
| 部署失敗 | Cloud Run 服務頁 →「修訂版本」→ 點失敗那筆 → 看 Cloud Build 記錄；多半是 build 錯誤，把紅字貼給 Claude Code。 |
| 網頁打得開但 API 全部錯 | Cloud Run 服務頁 →「記錄」分頁看 Python 錯誤。最常見是 `DATABASE_URL` 貼錯：確認開頭是 `postgresql+psycopg://`、結尾有 `sslmode=require`。 |
| 第一下打開很慢（5–10 秒） | 正常。執行個體下限 0 ＝閒置會歸零，下一次要冷啟動。介意的話把下限改 1（會開始產生常駐費用，約每月幾美元）。 |
| 導師回覆到一半斷線 | 確認步驟 4 的「要求逾時」有設 600 秒。 |
| Neon 連不上 | Neon 免費方案閒置會自動休眠，第一個請求會多等 1–2 秒喚醒，屬正常；持續失敗就到 Neon Dashboard 確認專案狀態、重新複製連線字串。 |
| 忘記 admin 密碼 | Neon Dashboard → SQL Editor 執行 `DELETE FROM users;` 後重新整理網站一次（會重新種 admin/admin）。⚠️ 這會刪掉所有帳號，僅單人使用時適用。 |

## 費用參考（個人低流量）

- **Cloud Run**：每月免費額度（vCPU 秒數/記憶體/請求數）對個人使用綽綽有餘；下限 0＋上限 1 的設定下通常 **$0**。
- **Cloud Build**：每日有免費建置分鐘數，個人 push 頻率下通常 **$0**。
- **Neon**：Free 方案（0.5 GB 儲存）足夠數萬則筆記，**$0**。
- **OpenAI API**：依用量計費，與部署無關（走你在設定頁註冊的 key）。

## （選用）綁自己的網域

Cloud Run 服務頁 → 上方「⋯」→ **管理自訂網域** → 新增對應 → 照指示到你的 DNS 服務商加一筆 CNAME 即可，憑證由 Google 自動簽發。
