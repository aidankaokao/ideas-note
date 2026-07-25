# Skill 設計慣例（SKILL.md · 可攜式）

> 專案裡若要設計「skill」（可重用、可被 agent / Claude 呼叫的能力模組），**一律採用 Claude 慣用的 `SKILL.md` 設計**：
> 一個 skill = 一個資料夾，內含一份帶 YAML frontmatter 的 `SKILL.md`（大寫），描述這個 skill 是什麼、何時用、怎麼用；需要的話再附腳本 / 參考檔。

---

## 0. 一句話總結

每個 skill 是**一個目錄**，裡面有一份 **`SKILL.md`**：最上方 YAML frontmatter 放 `name` + `description`（決定「何時觸發」），下方 Markdown 正文放「怎麼做」的指示與範例。**漸進揭露**：`SKILL.md` 精簡，細節 / 腳本另拆檔，用到才讀。

---

## 1. 目錄結構

```
backend/skills/
└── <skill-name>/                 # 目錄名 = skill 名（小寫連字號）
    ├── SKILL.md                  # 必要：入口，含 frontmatter + 指示
    ├── reference.md              # 選用：詳細規格 / API / 對照表（正文提到才讀）
    ├── scripts/                  # 選用：可執行輔助腳本
    │   └── run.py
    └── assets/                   # 選用：模板 / 範例檔
```

- **一個能力一個目錄**，目錄名用小寫連字號（kebab-case），與 frontmatter `name` 一致。
- `SKILL.md` **檔名必須大寫**。

---

## 2. `SKILL.md` 格式

```markdown
---
name: pdf-extract
description: 從 PDF 抽取文字與表格並轉成結構化 JSON。當使用者要讀取、解析、
  摘要 PDF，或把 PDF 內容轉成資料時使用。支援中文與掃描檔（走 OCR）。
---

# PDF 抽取

## 何時用
- 使用者上傳 / 指定 PDF 且要取其內容、表格、或做摘要時。
- 不用於：純文字檔（直接讀即可）、影像單張（用影像 skill）。

## 怎麼做
1. 先判斷是文字型還是掃描型 PDF（見 `reference.md` §1 判斷法）。
2. 文字型 → 用 `scripts/extract.py` 直接抽取。
3. 掃描型 → 走 OCR 流程（`scripts/ocr.py`）。
4. 表格輸出成 JSON，schema 見 `reference.md` §2。

## 範例
    python scripts/extract.py --in input.pdf --out result.json

## 注意
- 大檔（>50MB）先分頁處理，避免記憶體爆掉。
- 抽不到文字時回報「可能是掃描檔」，不要靜默回空。
```

**frontmatter 兩個必填欄位：**

| 欄位 | 作用 | 寫法要點 |
|---|---|---|
| `name` | skill 識別名 | 小寫連字號，與目錄名一致 |
| `description` | **觸發依據**（最重要）| 一句話講「做什麼」＋「**何時該用**」，用第三人稱、含具體關鍵字。呼叫方靠它判斷要不要載入這個 skill |

> `description` 寫得好不好，直接決定 skill 會不會在對的時機被叫用 —— 要把「使用者可能怎麼說 / 什麼情境」的關鍵字寫進去。

---

## 3. 漸進揭露（Progressive Disclosure）

不要把所有細節塞進 `SKILL.md`，避免一次載入過長。分三層：

1. **frontmatter**（`name` + `description`）—— 永遠先被看到，決定是否觸發。
2. **`SKILL.md` 正文** —— 觸發後讀，給「怎麼做」的流程與最常用範例，保持精簡。
3. **附檔**（`reference.md` / `scripts/` / `assets/`）—— 正文明確指引「見 xxx」時才讀 / 才執行。

原則：**`SKILL.md` 講判斷與流程，長規格與大表格丟 `reference.md`，可跑的邏輯丟 `scripts/`。**

---

## 4. 撰寫原則

- **命令式、給執行者看**：正文是寫給「之後要照做的 Claude / agent」看的指示，語氣明確（「先做 X，若 Y 則 Z」），不是行銷文案。
- **可執行優先**：能用腳本穩定完成的步驟就寫成 `scripts/`，正文只說何時呼叫、傳什麼參數，比讓模型每次重寫程式碼可靠。
- **邊界要寫清楚**：明講「何時用 / 何時不要用」，避免誤觸發。
- **範例具體**：附真實可跑的指令 / 輸入輸出樣例。
- **自足**：一個 skill 目錄自我包含，搬到別的專案可獨立運作。

---

## 5. 與本專案其他部分的關係

- skill 目錄放 `backend/skills/`（見 `backend-conventions.md` §4）。
- skill 內的邏輯若也被 API 用到，把真正的實作放 `services/`，`scripts/` 與 router 都去呼叫它，避免重複。
- 若 skill 由 LangGraph agent 觸發，agent 的 tool node 依 `SKILL.md` 的指示呼叫對應腳本 / service（見 `langgraph-agent.md`）。

---

## 6. 慣例小結

- **一 skill 一目錄**，內含大寫 `SKILL.md`（frontmatter `name` + `description` + 正文）。
- `description` 要含「做什麼 + 何時用」的關鍵字，這是觸發依據。
- **漸進揭露**：`SKILL.md` 精簡，細節拆 `reference.md`、邏輯拆 `scripts/`。
- 正文用命令式指示、邊界清楚、範例具體、目錄自足。
