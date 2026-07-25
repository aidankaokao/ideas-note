# UI 設計風格參考（Glass Wave）

供新專案直接沿用此版面風格。**僅淺色、不做深色模式**。主色藍。整體概念：**淡藍紫漸層背景 + 飄移光暈 + 玻璃感面板/卡片**。

## 技術棧
- React 18 + TypeScript + Vite
- Tailwind CSS（`tailwindcss-animate`）+ shadcn/ui 風格元件（自建，非整包）
- 圖示：`lucide-react`（線條 `strokeWidth={1.75}`）
- 字體：系統字（含中文）：`ui-sans-serif, system-ui, "Segoe UI", "Microsoft JhengHei", "PingFang TC", sans-serif`

---

## 一、配色與設計 Token（直接複製到 `index.css`）
色彩用 **HSL 變數**（`H S% L%`，搭配 Tailwind `hsl(var(--x))`）。

```css
:root {
  --background: 0 0% 100%;
  --foreground: 215 60% 15%;      /* 深藍灰文字 */
  --card: 0 0% 100%;
  --primary: 221 83% 53%;         /* 主色藍 #2563eb 系 */
  --primary-foreground: 0 0% 100%;
  --secondary: 214 32% 93%;
  --muted: 214 32% 93%;
  --muted-foreground: 215 16% 47%; /* 次要文字/灰 */
  --accent: 214 40% 94%;           /* hover 底色 */
  --destructive: 0 68% 55%;        /* 刪除紅 */
  --border: 214 32% 88%;
  --input: 214 32% 86%;
  --ring: 221 83% 53%;
  --radius: 0.875rem;              /* 圓角基準（卡片/對話框） */
  --success: 152 56% 42%;          /* 綠 */
  --warning: 38 92% 45%;           /* 琥珀 */
  --sidebar-border: 214 32% 88%;

  /* 背景漸層（固定不捲動）與飄移光暈 */
  --wave-bg: linear-gradient(135deg, #dbe6ff 0%, #e6dcff 50%, #dcf2ff 100%);
  --blob-1: rgba(147, 197, 253, 0.9);  /* 藍 */
  --blob-2: rgba(196, 181, 253, 0.9);  /* 紫 */
  --blob-3: rgba(110, 231, 183, 0.9);  /* 青綠 */
  --blob-opacity: 0.45;
  --blob-blur: 64px;
  --blob-blend: multiply;

  /* 玻璃感 */
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(15, 23, 42, 0.1);
  --glass-shadow: 0 6px 24px rgba(15, 23, 42, 0.1);
  --glass-inset: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
body {
  color: hsl(var(--foreground));
  background: var(--wave-bg);
  background-attachment: fixed;   /* 背景固定，內容捲動 */
  -webkit-font-smoothing: antialiased;
}
```

**Tailwind `theme.extend`**：把上面變數對應成 `colors`（border/input/ring/background/foreground/primary/secondary/muted/accent/destructive/card），並：
```ts
borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" }
```
狀態語意色：綠＝`--success`、琥珀＝`--warning`、紅＝`--destructive`；enum 標籤色票常用 green/amber/gray/red/blue。

---

## 二、玻璃感 / 光暈（utilities）
```css
.glass-card {   /* 卡片：半透明白 + 模糊 + 圓角 + 陰影 + 內光 */
  background: var(--glass-bg);
  backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius);
  box-shadow: var(--glass-shadow), var(--glass-inset);
}
.glass-panel {  /* 側邊欄/Header/Footer：更淡的玻璃白 */
  background: hsl(var(--background) / 0.72);
  backdrop-filter: blur(16px) saturate(150%);
}
.card-lift { transition: transform .18s, box-shadow .18s; }
.card-lift:hover { transform: translateY(-2px); }   /* 卡片 hover 上浮 */
.section-label {   /* 側邊欄分區小標 */
  font-size: 11px; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: hsl(var(--muted-foreground));
}
```
**動態背景**：`position:fixed; inset:0; z-index:-1` 的容器內放**三顆** `radial-gradient` 光暈（藍/紫/青），`filter: blur(64px)`、`mix-blend-mode: multiply`、`opacity .45`，各自 `@keyframes` 緩慢飄移/縮放（13～22s `ease-in-out infinite alternate`）。營造「活的」淡彩背景。

---

## 三、版面結構
```
<WaveBackground/>（fixed 背景光暈）
<div class="flex h-screen overflow-hidden">      // 整頁不捲動
  <Sidebar/>                                     // 左：可折疊/可拖曳寬
  <div class="flex flex-1 flex-col min-w-0">
    <Header/>                                    // 上：h-14 玻璃白
    <main class="flex-1 overflow-auto p-6">…</main>  // 只有主內容捲動
    <footer class="glass-panel border-t px-6 py-2">…</footer>  // 選用：分頁列放這
  </div>
</div>
```
重點：**外層 `h-screen overflow-hidden`，只有 `main` 捲動**；側邊欄與 header 固定。

---

## 四、側邊欄（Sidebar）
- **玻璃白底**（`glass-panel`）＋右側 1px `--sidebar-border`。
- **寬度可手動拖曳**：預設 `240px`，範圍 `180–480`，存 `localStorage`（key 如 `xxx-sidebar-w`）。
  - 拖曳感應區 `.sidebar-resizer`：**疊在側邊欄右緣的隱形直條**（`absolute; right:0; width:5px; height:100%; cursor:col-resize; 背景透明`），**hover / 拖曳中才變藍**（`hsl(var(--primary)/.4)`）。滑鼠拖曳時 `body { user-select:none }`。
- **可折疊**：展開＝記憶寬度；折疊＝固定 `64px`（只剩 icon、置中）。折疊切換鈕放 **Header 左側**，用方向性 icon：`PanelLeftClose`（展開時）/`PanelLeftOpen`（折疊時，lucide）。
- 內容：頂部品牌區（`h-14`，方形 logo chip `bg-primary/15 text-primary`）＋分區（用 `.section-label`：Dashboard / 管理 …）＋導覽項。
- **導覽項**：`h-9 rounded-md px-3 text-sm`；**選中**＝膠囊 `bg-primary/15 font-semibold text-primary`；未選＝`text-muted-foreground hover:bg-accent`。icon `18px`。

---

## 五、Header
- `h-14`、玻璃白（`glass-panel`）、下緣 1px border。
- 左：側邊欄折疊鈕（方向 icon）。中/左：**頁面標題 + 副標題**（副標 `text-muted-foreground`，字級小）。右：角色 chip、登出 icon 鈕。
- 頁面標題採「集中式」：由各頁透過一個 store/hook 設定（標題＋副標），Header 讀取顯示（平台名稱只放側邊欄）。

---

## 六、卡片 / 對話框 / 表格
- **卡片**：`glass-card`（圓角 `--radius` ≈ 14px）；內距 `p-5`；標題 `text-[15px] font-semibold`；需要浮起感再加 `card-lift`。
- **對話框（Dialog）**：白底、`rounded-xl`、`shadow-lg`、`max-h-[90vh] overflow-y-auto`、置中。
  - **近滿版樣式**（大型編輯器用）：`w-[94vw] max-w-[1480px] h-[90vh] flex flex-col`。
  - **第二層懸浮框**：可在 Dialog 內再開 Dialog（巢狀），用於「設定裡的細項設定」。
- **表格**：統一 class `.tbl`：`font-size:13px; line-height:1.35`；`th/td padding: .5rem .75rem; white-space:nowrap`（過寬水平捲動，不擠成多行）；表內 icon 鈕縮成 `1.75rem`。表頭可 `sticky top-0 bg-muted/60`。
- **捲軸**：細版 `6px`，`thumb` 用 `muted-foreground/.25`、圓角。

---

## 七、通用互動慣例
- **圖示**一律 lucide，線條 `strokeWidth={1.75}`；操作用 icon-only 鈕（編輯 `Pencil`、刪除 `Trash2` 紅、複製 `Copy`、上傳 `Upload`、刷新 `RefreshCw`、展開/收合 `ChevronDown/Up`）。
- **Toast**：輕量（Zustand store + 固定角落），操作完成/失敗即時回饋；成功綠、錯誤紅。
- **危險操作二次確認**：刪除重要資料用「輸入 `DELETE` 才可確認」的對話框。
- **多秒操作進度**：底部中央非阻擋小卡（`Loader2` 轉圈 + 步驟文字），完成再跳結果框；避免只用會閃掉的 toast。
- **分頁**：放在全域 footer；元件含「共 N 筆 + 每頁筆數選單 + 上/下頁 icon + 可輸入頁碼跳轉」。
- **狀態標籤**：enum 值可設色（green/amber/gray/red/blue）以彩色小標籤呈現；bool 可設 ✓/✗ 或 是/否 樣式。

---

## 八、一句話抓風格
> 淡藍紫漸層 + 飄移光暈背景，前景是**半透明玻璃白**的側邊欄/Header/卡片；主色藍、圓角約 14px、線條 icon、細捲軸；側邊欄可拖寬可折疊；只有主內容區捲動。整體清爽、通透、專業。

> 新專案套用時：先貼上第一、二節的 CSS token 與 utilities、設定 Tailwind `theme.extend`，再依第三～六節搭版面與元件，即可還原此風格。
