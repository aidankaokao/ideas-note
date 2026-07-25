# 前端設計風格指南（可攜式）

> 這份文件把本專案的**前端視覺 / 互動風格**抽離成一份自足的規範，  
> 目的是：**新的 Claude Code session 只看這一份，就能在全新專案裡完全重現同一種風格。**  
> 只談前端外觀與互動，不涉及任何後端功能。

---

## 0. 一句話總結風格

**乾淨、專業、資訊密集的後台工具風（dashboard / SaaS console）**：
- 白底、石板灰（slate）中性色、單一主色點綴
- 圓角柔和（`0.5rem`）、細邊框、極淡陰影
- 主色透過 CSS 變數統一控制，**可一鍵切換 7 種主題色**
- 側邊欄可**拖曳調寬 + 折疊**（折疊鈕在主 header 左上角），底部固定**版本號 / 版本履歷**
- 大量使用 shadcn/ui 元件 + Radix primitives
- 狀態語意色固定：amber=警告、emerald/green=成功、rose/red=危險、blue=資訊

---

## 1. 技術棧（先裝這些）

```
React 18 + TypeScript + Vite
Tailwind CSS 3.4
shadcn/ui 元件（複製到 src/components/ui/）
Radix UI primitives（dialog / select / tabs / dropdown / switch / toast...）
lucide-react（icon，唯一 icon 來源）
class-variance-authority（cva，做元件 variant）
clsx + tailwind-merge（合成 cn() helper）
zustand（狀態管理，非樣式相關）
recharts（圖表）
```

`package.json` 關鍵 dependencies：

```jsonc
"@radix-ui/react-dialog": "^1.0.5",
"@radix-ui/react-select": "^2.0.0",
"@radix-ui/react-tabs": "^1.0.4",
"@radix-ui/react-dropdown-menu": "^2.0.6",
"@radix-ui/react-switch": "^1.0.3",
"@radix-ui/react-toast": "^1.1.5",
"class-variance-authority": "^0.7.0",
"clsx": "^2.1.0",
"tailwind-merge": "^2.2.1",
"tailwindcss-animate": "^1.0.7",
"lucide-react": "^0.344.0"
```

**核心 helper — 每個元件都用它合 className：**

```ts
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## 2. 顏色系統（重點！用 HSL CSS 變數，不要寫死顏色）

顏色**全部**走 CSS 變數，元件只引用語意名稱（`bg-primary`、`text-muted-foreground`），**不直接寫 hex**。這是能「一鍵換主題色」的關鍵。

### 2.1 `src/index.css` — 貼上這整段

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;          /* 預設藍 */
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;                       /* 全域圓角基準 */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * { @apply border-border; }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

/* 細捲軸（6px、半透明、hover 加深）— 全站統一 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: hsl(var(--muted)); }
::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
```

> 注意：變數值是「**裸 HSL 三數值**」（如 `221.2 83.2% 53.3%`），不含 `hsl()`。  
> Tailwind config 用 `hsl(var(--x))` 包起來，所以還能用 `/50` 這種 alpha 語法（`bg-primary/90`）。

### 2.2 語意色速查

| 語意 token | 用途 | 典型 class |
|---|---|---|
| `background` / `foreground` | 頁面底 / 主文字 | `bg-background text-foreground` |
| `card` | 卡片底色（同白） | `bg-card` |
| `primary` | 主色（按鈕、active、重點） | `bg-primary text-primary-foreground` |
| `secondary` | 次要按鈕 / 淡底 | `bg-secondary` |
| `muted` / `muted-foreground` | 淡底塊 / 說明文字 | `text-muted-foreground` |
| `accent` | hover 底色 | `hover:bg-accent` |
| `destructive` | 危險 / 刪除 | `bg-destructive` |
| `border` / `input` | 邊框 / 輸入框框線 | `border-border` |
| `ring` | focus 外框 | `focus-visible:ring-ring` |

### 2.3 狀態語意色（直接用 Tailwind 色階，固定慣例）

| 狀態 | 底 | 文字 | 邊框 | icon |
|---|---|---|---|---|
| 資訊 / 選中 | `bg-blue-50` | `text-blue-700` | `border-blue-200` | blue |
| 警告 / 需注意 | `bg-amber-50` | `text-amber-700` | `border-amber-200` | `text-amber-500` |
| 成功 | `bg-emerald-50` / `bg-green-100` | `text-green-800` | `border-emerald-200` | emerald/green |
| 危險 / 錯誤 | `bg-rose-50` / `bg-red-50` | `text-red-600` | `border-red-200` | red |
| 中性 / 側欄底 | `bg-slate-50` | `text-slate-600` | `border-slate-200` | slate |

慣例：淡底用 `-50`、文字用 `-600/700/800`、hover 前景 `hover:text-slate-900`。  
「未選中」互動元素常見組合：`text-slate-600 hover:bg-slate-100 hover:text-slate-900`。

---

## 3. Tailwind Config（`tailwind.config.ts`）

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary:     { DEFAULT: "hsl(var(--primary))",     foreground: "hsl(var(--primary-foreground))" },
        secondary:   { DEFAULT: "hsl(var(--secondary))",   foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted:       { DEFAULT: "hsl(var(--muted))",       foreground: "hsl(var(--muted-foreground))" },
        accent:      { DEFAULT: "hsl(var(--accent))",      foreground: "hsl(var(--accent-foreground))" },
        popover:     { DEFAULT: "hsl(var(--popover))",     foreground: "hsl(var(--popover-foreground))" },
        card:        { DEFAULT: "hsl(var(--card))",        foreground: "hsl(var(--card-foreground))" },
      },
      borderRadius: {
        lg: "var(--radius)",                    // 0.5rem = 8px
        md: "calc(var(--radius) - 2px)",        // 6px
        sm: "calc(var(--radius) - 4px)",        // 4px
      },
      keyframes: {
        "accordion-down": { from: { height: "0" }, to: { height: "var(--radix-accordion-content-height)" } },
        "accordion-up":   { from: { height: "var(--radix-accordion-content-height)" }, to: { height: "0" } },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

**圓角規則（很重要，全站一致）：**
- `--radius: 0.5rem`（8px）是基準
- 卡片 / 大容器 → `rounded-lg`（8px）
- 按鈕 / 輸入框 / 下拉 / 中型元件 → `rounded-md`（6px）
- Tab trigger / 小元件 → `rounded-sm`（4px）
- Badge / 標籤 / 圓點 → `rounded-full`
- icon 按鈕 hover 底 → `rounded`（預設 4px）

---

## 4. 可切換主題色（7 色，一鍵套用）

只覆寫 `--primary` 與 `--ring` 兩個變數，其餘中性色不動 → 全站重點色即時跟著變。

```ts
// App.tsx
const THEME_COLORS: Record<string, { primary: string; ring: string }> = {
  blue:   { primary: "221.2 83.2% 53.3%", ring: "221.2 83.2% 53.3%" },
  green:  { primary: "142.1 76.2% 36.3%", ring: "142.1 76.2% 36.3%" },
  purple: { primary: "262.1 83.3% 57.8%", ring: "262.1 83.3% 57.8%" },
  orange: { primary: "24.6 95% 53.1%",    ring: "24.6 95% 53.1%" },
  red:    { primary: "0 84.2% 60.2%",     ring: "0 84.2% 60.2%" },
  teal:   { primary: "172.5 66% 50.4%",   ring: "172.5 66% 50.4%" },
  slate:  { primary: "215.4 16.3% 46.9%", ring: "215.4 16.3% 46.9%" },
};

function applyTheme(color: string) {
  const t = THEME_COLORS[color] || THEME_COLORS.blue;
  document.documentElement.style.setProperty("--primary", t.primary);
  document.documentElement.style.setProperty("--ring", t.ring);
}
```

因此所有「重點」都必須用 `bg-primary` / `text-primary` / `ring-ring`，**絕不寫死藍色**，否則換主題不會生效。  
（例外：語意狀態色 amber/emerald/rose 是固定的，不跟主題。）

---

## 5. 版面骨架（AppShell：可拖曳 + 可折疊側邊欄）

整體是 **左側邊欄 + 右主內容** 的經典 dashboard 佈局。

### 5.1 側邊欄行為
- 預設寬 `220px`，可拖曳範圍 `160 ~ 400px`；**寬度與 collapsed 狀態都持久化 `localStorage`**
- 右緣有 1px 拖曳把手，hover 變藍（`hover:bg-blue-400`）
- 側欄 `sticky top-0 h-screen`，內部自己捲動

**折疊鈕（icon、位置、邏輯）**
- **位置**：放在**主內容區頂部工具列（header）的左上角**，*不*放在側邊欄裡——這樣即使側欄收合，鈕仍點得到。
- **icon**：lucide `PanelLeftClose`（目前為展開、點了會收合）／ `PanelLeftOpen`（目前為收合、點了會展開），`h-4 w-4`，用 ghost icon button（`hover:bg-muted rounded-md`）。
- **邏輯**：只切換 `collapsed` 布林，**不動側欄寬度**（展開時回到記憶的寬度）；`title` 隨狀態切換 `"Collapse sidebar"` / `"Expand sidebar"`。
- **收合模式（二選一）**：
  - (A) **完全隱藏**側欄（下方 AppShell 範例採此法，`!collapsed && <Sidebar/>`）。
  - (B) **縮為固定 `52px` 的 icon rail**：側欄不消失，只保留每列的 icon、隱藏文字 / 表單 / 版本號文字（資訊密集型後台常用；收合時把文字節點以 `{!collapsed && <span>…</span>}` 條件渲染即可）。

```tsx
// 頂部工具列的折疊鈕（放在主內容區 header 左上，見下方 AppShell 的 <main> 內）
<button
  type="button"
  onClick={() => setCollapsed((v) => !v)}
  title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
  className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
>
  {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
</button>
```

```tsx
// components/layout/AppShell.tsx（核心邏輯）
const MIN_WIDTH = 160, MAX_WIDTH = 400, DEFAULT_WIDTH = 220;

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_WIDTH);
  const dragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(DEFAULT_WIDTH);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    startX.current = e.clientX;
    startWidth.current = sidebarWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const delta = e.clientX - startX.current;
      const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth.current + delta));
      setSidebarWidth(next);
    };
    const onMouseUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }, [sidebarWidth]);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {!collapsed && (
        <div className="relative flex-none flex">
          <Sidebar width={sidebarWidth} />
          {/* 拖曳把手 */}
          <div
            onMouseDown={onMouseDown}
            className="w-1 cursor-col-resize hover:bg-blue-400 active:bg-blue-500 transition-colors bg-border flex-none"
            title="拖曳調整寬度"
          />
        </div>
      )}

      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* 頂部工具列：折疊鈕，半透明毛玻璃底 */}
        <div className="flex-none z-10 flex items-center gap-2 px-4 py-2 bg-background/95 backdrop-blur border-b border-border">
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            {collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
          </button>
        </div>
        {/* 內容捲動容器 */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          <Outlet />
        </div>
      </main>

      <Toaster />
    </div>
  );
}
```

### 5.2 側邊欄本體（Sidebar）

- 底色 `bg-slate-50`，右邊框 `border-slate-200`
- 三段式：Logo/標題（頂）→ 導航（中，可捲）→ 版本號（底）
- 導航項 active 用 `bg-primary text-white shadow-sm`，非 active 用 `text-slate-600 hover:bg-slate-200`
- 導航項圓角 `rounded-lg`，item 之間 `space-y-0.5`
- 每項左側 lucide icon（`h-4 w-4 shrink-0`）+ 文字（`truncate`）

```tsx
<aside
  className="bg-slate-50 border-r border-slate-200 flex flex-col h-screen sticky top-0 overflow-hidden"
  style={{ width }}
>
  {/* 標題列 */}
  <div className="px-4 py-4 border-b border-slate-200">
    <div className="flex items-center gap-2">
      <ClipboardList className="h-5 w-5 text-primary shrink-0" />
      <span className="font-bold text-sm tracking-wide text-slate-800 truncate">產品名稱</span>
    </div>
  </div>

  {/* 導航 */}
  <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
    {navItems.map(({ to, icon: Icon, label }) => (
      <NavLink
        key={to}
        to={to}
        className={({ isActive }) =>
          cn(
            "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
            isActive
              ? "bg-primary text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-200 hover:text-slate-900"
          )
        }
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span className="truncate">{label}</span>
      </NavLink>
    ))}
  </nav>

  {/* 版本號 + 版本履歷（底部固定，見 §5.3） */}
  <VersionFooter collapsed={collapsed} />
</aside>
```

---

### 5.3 側邊欄底部：版本號 + 版本履歷

側邊欄**最底部**固定顯示目前版本號，**雙擊**後展開「版本履歷（changelog）」。這是純前端互動模式；資料來源（`localStorage` / API / store）可自由替換，本節只規範**外觀與互動**。

**顯示規則**
- 一律以 `border-t` 與導航區分隔；展開時 `px-3 py-2.5`，收合時 `flex items-center justify-center h-10`。
- 版本號用 mono 小字：`text-[11px] font-mono text-slate-400`，前綴固定 `v`（例：`v0.0.2`）。
- 目前版本 = 履歷陣列的**第一筆（最新新增）**；陣列為空時顯示預設 `v0.0.1`。
- 側欄**收合時**只顯示一個 `Tag` icon（`h-3.5 w-3.5`），隱藏版本文字。
- `cursor-pointer select-none` + `title="Double-click to view version history"`。

**互動流程（雙擊 → 最多三層 Dialog）**

| 層 | 觸發 | 內容 |
|---|---|---|
| （可選）密碼層 | 雙擊版本號 | 若要限制編輯權限，先跳一層密碼 Dialog；驗證通過才進入履歷層。前端只負責 UI + 呼叫驗證，驗證邏輯交給外部（API / props）。錯誤時輸入框 `border-destructive` + `animate-shake` |
| 第一層：履歷列表 | 密碼通過 / 直接雙擊 | 逐筆列出版本（`Badge` 顯示 `vX.X.X` + 日期 + 標題 + `<ul className="list-disc">` 條列 items）；空狀態顯示「No version records yet.」；底部一顆「Add Version」按鈕；每筆 hover 才出現刪除鈕（`opacity-0 group-hover:opacity-100`） |
| 第二層：新增表單 | 點「Add Version」 | 欄位：版本號（輸入 `0.0.2` → 顯示 `v0.0.2`）、日期（`DatePicker`）、標題、履歷項目（每項一個 `Input`，`+` 動態增列、`Trash2` 逐列刪除）；「完成」送出後回到第一層即看到新版本 |

**版本履歷條目（型別）**

```ts
interface VersionEntry {
  id: string;
  version: string; // "0.0.2"（顯示時前綴 v）
  date: string;    // YYYY-MM-DD
  title: string;
  items: string[]; // 條列變更
}
```

**版本號 footer（元件骨架）**

```tsx
function VersionFooter({ collapsed }: { collapsed: boolean }) {
  const [versions, setVersions] = useState<VersionEntry[]>([]); // 來源可換成 API / store
  const [historyOpen, setHistoryOpen] = useState(false);
  const current = versions.length ? versions[0].version : "0.0.1";

  return (
    <>
      <div
        className={cn(
          "border-t border-slate-200 select-none cursor-pointer text-slate-400 hover:text-slate-700 transition-colors",
          collapsed ? "flex items-center justify-center h-10" : "px-3 py-2.5"
        )}
        onDoubleClick={() => setHistoryOpen(true)}
        title="Double-click to view version history"
      >
        {collapsed ? (
          <Tag className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <div className="flex items-center gap-1.5 text-[11px] font-mono">
            <Tag className="h-3 w-3 shrink-0" />
            <span>v{current}</span>
          </div>
        )}
      </div>

      {/* 第一層：履歷列表 Dialog（用 §7.6 Dialog）
          第二層：新增表單 Dialog（版本號 / 日期 / 標題 / items[]，見下方動態項目列） */}
    </>
  );
}
```

**新增表單裡的「動態項目列」**（`+` 新增、逐列刪除）——資訊密集後台常見模式：

```tsx
const [items, setItems] = useState<string[]>([""]);
const addItem = () => setItems((a) => [...a, ""]);
const setItem = (i: number, v: string) => setItems((a) => a.map((x, idx) => (idx === i ? v : x)));
const delItem = (i: number) => setItems((a) => a.filter((_, idx) => idx !== i));

{items.map((it, i) => (
  <div key={i} className="flex items-center gap-2">
    <Input value={it} onChange={(e) => setItem(i, e.target.value)} placeholder={`Item ${i + 1}`} />
    <button type="button" onClick={() => delItem(i)}
      className="shrink-0 text-slate-400 hover:text-red-600 transition-colors">
      <Trash2 className="h-4 w-4" />
    </button>
  </div>
))}
<Button type="button" variant="ghost" size="sm" onClick={addItem}>
  <Plus className="h-3.5 w-3.5 mr-1" /> Add
</Button>
```

> 兩層（或含密碼三層）Dialog 直接用 §7.6 的 shadcn `Dialog` 疊加即可：各層用自己的 `open` state 獨立控制、彼此可獨立關閉，Radix 會自動處理 focus 疊層。

---

## 6. 頁面內容佈局規範

每個頁面外層固定用：

```tsx
<div className="p-6 space-y-6">
  {/* Header：標題 + 說明 靠左，主要動作按鈕靠右 */}
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-2xl font-bold">頁面標題</h1>
      <p className="text-muted-foreground text-sm mt-1">一句話說明這頁在做什麼</p>
    </div>
    <Button type="button">
      <Plus className="h-4 w-4 mr-2" />
      主要動作
    </Button>
  </div>

  {/* 內容區 */}
</div>
```

間距慣例：
- 頁面 padding：`p-6`
- 區塊之間：`space-y-6`（大）/ `space-y-4`（中）/ `space-y-2`（小）
- 卡片內 padding：`p-6`（`CardHeader` / `CardContent` 預設）
- 並排容器間距：`gap-4`
- 頁標題 `text-2xl font-bold`；區塊小標 `text-xl font-semibold` / `text-sm font-medium`
- 說明文字一律 `text-muted-foreground text-sm`

「頁內二級側欄」（如資料夾清單）常見寬度 `w-48 shrink-0`，項目：

```tsx
<button className={cn(
  "w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 transition-colors",
  active ? "bg-blue-50 text-blue-700 font-medium" : "text-slate-600 hover:bg-slate-100"
)}>
  <Folder className="h-4 w-4 shrink-0" />
  <span className="truncate flex-1">名稱</span>
  <span className="ml-auto text-xs text-slate-400">{count}</span>
</button>
```

---

## 7. 核心 UI 元件（shadcn 版本，直接複製）

> 全部放 `src/components/ui/`。以下是本專案實際使用的版本，風格已定型。

### 7.1 Card — 圓角 8px、細框、極淡陰影

```tsx
const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />
  )
);
// CardHeader: "flex flex-col space-y-1.5 p-6"
// CardTitle:  "text-2xl font-semibold leading-none tracking-tight"
// CardDescription: "text-sm text-muted-foreground"
// CardContent: "p-6 pt-0"
// CardFooter:  "flex items-center p-6 pt-0"
```

卡片視覺 DNA：**`rounded-lg border bg-card shadow-sm`**。需要 hover 抬升時加 `hover:shadow-md transition-shadow`。

### 7.2 Button — cva variant

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:     "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:     "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:   "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost:       "hover:bg-accent hover:text-accent-foreground",
        link:        "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);
```

按鈕內有 icon 時：`<Icon className="h-4 w-4 mr-2" />` 接文字。

### 7.3 Badge — 圓角膠囊、含 success/warning 語意

```tsx
const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:     "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:   "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline:     "text-foreground",
        success:     "border-transparent bg-green-100 text-green-800",
        warning:     "border-transparent bg-yellow-100 text-yellow-800",
      },
    },
    defaultVariants: { variant: "default" },
  }
);
```

### 7.4 Input — 高 40px、`rounded-md`、focus ring

```tsx
"flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
```

（緊湊場景用 `className="h-7 text-xs"` 覆寫成小尺寸。）

### 7.5 Tabs — 灰底藥丸容器，active 白底浮起

```tsx
// TabsList
"inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground"
// TabsTrigger
"inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all ... data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
```

### 7.6 Dialog — 置中、`max-w-lg`、`sm:rounded-lg`、深色 overlay + 淡入縮放動畫

```tsx
// Overlay
"fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
// Content
"fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in ... data-[state=open]:zoom-in-95 ... sm:rounded-lg"
// 右上角關閉鈕：absolute right-4 top-4 + <X className="h-4 w-4" />
// DialogTitle: "text-lg font-semibold leading-none tracking-tight"
```

**全螢幕級 Dialog**（大表格 / 編輯器）慣例：`className="max-w-[96vw] h-[94vh]"` + 內層 `flex flex-col` + 內容 `overflow-y-auto`。

### 7.7 Select — 高 40px、`rounded-md`、右側 ChevronDown

Trigger：
```tsx
"flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1"
```

> Radix `<SelectItem>` 的 `value` **不可為空字串**，需要「無」選項時用哨兵值如 `"__none__"`。

---

## 8. 互動 / 動效慣例

- **一律加 `transition-colors`**（或 `transition-all`）在會變色的互動元素上，時間用預設。
- focus 統一：`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`。
- disabled 統一：`disabled:pointer-events-none disabled:opacity-50`。
- **hover 才顯示的操作鈕**（列表列上的編輯/刪除）：父層 `group`，子鈕 `opacity-0 group-hover:opacity-100 transition-all`。
- Dialog 動畫用 `tailwindcss-animate` 的 `data-[state=open]:animate-in ... zoom-in-95 fade-in-0`。
- 毛玻璃頂列：`bg-background/95 backdrop-blur`。
- icon 按鈕 hover：`hover:bg-muted` 或 `hover:bg-accent` + `rounded-md`。

---

## 9. 折疊區塊（兩種做法）

**輕量摺疊**（表單進階選項、context 摘要）→ 原生 `<details>`：

```tsx
<details className="text-sm">
  <summary className="cursor-pointer text-muted-foreground hover:text-foreground select-none">
    進階設定
  </summary>
  <div className="mt-2 space-y-2">{/* ... */}</div>
</details>
```

**受控展開/收合**（卡片列表全展開/全收合）→ 自己用 `useState(false)` 控制，預設**收合**，箭頭 icon 旋轉。

---

## 10. Icon 規範（lucide-react）

- **唯一 icon 來源**：`lucide-react`，不混用其他 icon 庫。
- 尺寸慣例：導航/內文 `h-4 w-4`；頂列按鈕 `h-5 w-5`；小徽章/inline `h-3 w-3` / `h-3.5 w-3.5`。
- icon 恆加 `shrink-0` 避免被壓縮。
- 常用語意 icon：`Plus`(新增) `Pencil`(編輯) `Trash2`(刪除) `Check`(確認) `X`(取消/關閉) `Settings` `Database` `FileText` `HelpCircle` `PanelLeftClose/Open`(折疊) `Lock` `AlertTriangle`(警告) `ChevronDown` `Tag`(版本號)。

---

## 11. Toast（通知）

- 用 Radix Toast + shadcn `useToast`，`<Toaster />` 掛在 AppShell 最外層。
- 成功：預設樣式；失敗：`variant: "destructive"` + 較長 `duration: 10000`。

```ts
toast({ title: "已儲存" });
toast({ title: "上傳失敗", description: msg, variant: "destructive", duration: 10000 });
```

---

## 12. 給新 session 的「照做」清單

要把這套風格搬到新專案，依序做：

1. 建 Vite + React + TS 專案，裝 §1 依賴。
2. 貼上 §2.1 `index.css`、§3 `tailwind.config.ts`、`postcss.config.js`（autoprefixer + tailwindcss）。
3. 建 `src/lib/utils.ts` 的 `cn()`（§1）。
4. 從 §7 複製 `ui/`：`card / button / badge / input / select / tabs / dialog / dropdown-menu / switch / toast + toaster`。
5. 建 `AppShell`（§5.1 可拖曳折疊，折疊鈕在 header 左上）+ `Sidebar`（§5.2）+ 底部 `VersionFooter`（§5.3 版本號 / 版本履歷）。
6. 若要主題切換，貼 §4 的 `THEME_COLORS` + `applyTheme`。
7. 頁面一律照 §6 骨架：`p-6 space-y-6` + 標題列 + 卡片內容。
8. 全程遵守：**重點色用 `bg-primary`（不寫死）、圓角照 §3、狀態色照 §2.3、互動加 `transition-colors` + 統一 focus ring、icon 用 lucide 加 `shrink-0`。**

> 一句判準：畫面看起來像「乾淨的白底 SaaS 後台、單一主色點綴、slate 中性灰、柔和圓角、細邊框淡陰影」就對了。
```
