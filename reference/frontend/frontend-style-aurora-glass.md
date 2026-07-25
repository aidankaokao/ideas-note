# 前端設計風格指南（Aurora Glass 極光琉璃 · 可攜式）

> 這份文件把 **Aurora Glass（極光琉璃）** 的前端視覺 / 互動風格抽離成一份自足規範，
> 目的是：**新的 Claude Code session 只看這一份，就能在全新專案裡完全重現同一種風格。**
> 只談前端外觀與互動，不涉及任何後端功能。

---

## 0. 一句話總結風格

**清新通透的毛玻璃風（glassmorphism）**：
- 淺色系背景 + 冷色漸光光暈（teal → indigo），**只做淺色、預設不做深色模式**
- 前景一律 **半透明毛玻璃白**（`.glass`），透出背後漂浮光暈
- 大圓角（`--radius: 1rem`，卡片 `rounded-3xl` ≈ 24px）、柔擴散陰影、無銳利黑邊
- 重點元素（主 CTA、圖示方塊、標題關鍵詞、項目符號）貫穿 **teal → indigo 品牌漸層**
- 主色 indigo；品牌漸層與配色用 CSS 變數統一控制，**可一鍵切換多套主題盤**
- 背景光暈緩慢漂浮、內容 fade-up 進場，但克制、不喧賓奪主

> **給 AI 的風格開場白（可直接複製當 prompt）**
> 請用 **Aurora Glass（極光琉璃）** 風格設計介面 —— 玻璃質感清新風：淺色背景配柔和漸層光暈、frosted-glass 半透明卡片、大圓角、teal→indigo 品牌漸層、細膩陰影與微動畫。整體通透、乾淨、現代、留白充足。**嚴格套用本文件的 CSS 變數、`.glass` 系列、圓角與漸層數值**；不要用不透明實心卡片、不要重陰影、不要濃飽和背景。

---

## 1. 技術棧（先裝這些）

```
React 18 + TypeScript + Vite
Tailwind CSS 3.4 + tailwindcss-animate
shadcn/ui 風格元件（自建到 src/components/ui/，非整包安裝）
lucide-react（icon，唯一 icon 來源，線條 strokeWidth={1.75}）
class-variance-authority（cva，做元件 variant）
clsx + tailwind-merge（合成 cn() helper）
sonner（toast 通知）
```

`package.json` 關鍵 dependencies：

```jsonc
"class-variance-authority": "^0.7.0",
"clsx": "^2.1.0",
"tailwind-merge": "^2.2.1",
"tailwindcss-animate": "^1.0.7",
"lucide-react": "^0.344.0",
"sonner": "^1.4.0"
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

## 2. 顏色系統（HSL CSS 變數，不要寫死顏色）

顏色**全部**走 CSS 變數，元件只引用語意名稱（`bg-primary`、`text-muted-foreground`），**不直接寫 hex**。品牌漸層也走變數（`--brand-*`），這是能「一鍵換主題盤」的關鍵。

### 2.1 `src/index.css` — `:root` tokens

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 200 60% 98%;        /* #F5FAFC 頁面底 */
    --foreground: 222 30% 18%;        /* #20293B 主文字（深藍灰）*/
    --card: 210 40% 100%;             /* 卡片基底（實際靠 .glass 半透明化）*/
    --card-foreground: 222 30% 18%;
    --popover: 210 40% 100%;
    --popover-foreground: 222 30% 18%;
    --primary: 244 68% 62%;           /* #655CE0 主色 indigo */
    --primary-foreground: 210 40% 99%;
    --secondary: 180 45% 92%;         /* #DCF2F1 次要淺面 */
    --secondary-foreground: 200 40% 22%;
    --muted: 210 30% 94%;             /* #EBF0F4 靜音背景 */
    --muted-foreground: 215 18% 46%;  /* #6A7789 次級/說明文字 */
    --accent: 172 66% 80%;            /* #A6EDE3 點綴（teal 淺）*/
    --accent-foreground: 200 45% 20%;
    --destructive: 0 72% 58%;         /* #E14444 刪除/危險 */
    --destructive-foreground: 210 40% 99%;
    --border: 214 32% 88%;            /* #D6DEE8 */
    --input: 214 32% 88%;
    --ring: 244 68% 62%;              /* = primary，focus 環 */
    --radius: 1rem;                   /* 圓角基準（偏大）*/

    /* 品牌漸層（核心識別，務必走變數）*/
    --brand-from: #14B8A6;            /* teal-500 */
    --brand-to:   #6366F1;            /* indigo-500 */

    /* 背景光暈 blob 顏色（GlassBackground 讀取）*/
    --glow-1: 172 70% 60%;            /* teal（左上）*/
    --glow-2: 244 80% 72%;            /* indigo（右上）*/
    --glow-3: 205 90% 72%;            /* sky（下中）*/

    /* body 三層背景漸層（切主題時覆寫）*/
    --bg-a: 180 80% 92%;             /* 左上偏 teal 光 */
    --bg-b: 250 90% 94%;             /* 右上偏 indigo 光 */
    --bg-c: 205 60% 98%;             /* 底漸層起 */
    --bg-d: 230 55% 96%;             /* 底漸層迄 */
  }
}
```

> 變數值是「**裸 HSL 三數值**」（如 `244 68% 62%`），不含 `hsl()`。
> Tailwind config 用 `hsl(var(--x))` 包起來，所以還能用 `/50` alpha 語法（`bg-primary/10`）。
> 品牌漸層例外用 hex（`--brand-from/to`），方便 `linear-gradient` 直接吃。

### 2.2 語意色速查

| 語意 token | 用途 | 典型 class |
|---|---|---|
| `background` / `foreground` | 頁面底 / 主文字 | `bg-background text-foreground` |
| `card` | 卡片基底（配 `.glass` 半透明）| `.glass` |
| `primary` | 主色 indigo（按鈕、focus、強調）| `bg-primary text-primary-foreground` |
| `secondary` | 次要淺面 | `bg-secondary` |
| `muted` / `muted-foreground` | 靜音底 / 說明文字 | `text-muted-foreground` |
| `accent` | teal 淺點綴 / hover | `bg-accent` |
| `destructive` | 危險 / 刪除 | `bg-destructive` |
| `border` / `input` | 邊框 / 輸入框線 | `border-border` |
| `ring` | focus 外框 | `focus-visible:ring-ring` |

### 2.3 狀態語意色

以品牌 teal / indigo 為主軸，狀態沿用 Tailwind 色階：綠=成功、琥珀=警告、紅=`destructive`、藍=資訊。
Badge 常用彩票：`teal`（teal-500/15 text-teal-700）、`indigo`（indigo-500/15 text-indigo-700）、`green`、`amber`、`muted`。淡底用 `/10~/15`、文字用 `-600/700`。

---

## 3. 背景（body 三層 + 漂浮光暈）

### 3.1 `body` 背景（`index.css`，`background-attachment: fixed`）

```css
@layer base {
  * { @apply border-border; }
  body {
    @apply text-foreground;
    background:
      radial-gradient(1200px 800px at 10% -10%, hsl(var(--bg-a)) 0%, transparent 55%),
      radial-gradient(1000px 700px at 100% 0%, hsl(var(--bg-b)) 0%, transparent 55%),
      linear-gradient(180deg, hsl(var(--bg-c)) 0%, hsl(var(--bg-d)) 100%);
    background-attachment: fixed;   /* 背景固定，只有內容捲動 */
    -webkit-font-smoothing: antialiased;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto,
                 "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
  }
}
```

> 左上偏 teal、右上偏 indigo、整體淺藍白漸層 → 冷色清新基調。

### 3.2 漂浮光暈 `GlassBackground.tsx`（掛在最外層）

固定滿版、`-z-10`、`pointer-events-none`，三顆大圓 `blur-3xl` + `animate-blob`，交錯 `animation-delay`：

```tsx
// components/GlassBackground.tsx
export function GlassBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute -top-24 -left-24 h-[42rem] w-[42rem] rounded-full blur-3xl animate-blob"
           style={{ background: "hsl(var(--glow-1) / 0.40)" }} />
      <div className="absolute -top-16 right-[-8rem] h-[38rem] w-[38rem] rounded-full blur-3xl animate-blob"
           style={{ background: "hsl(var(--glow-2) / 0.40)", animationDelay: "6s" }} />
      <div className="absolute bottom-[-10rem] left-1/3 h-[36rem] w-[36rem] rounded-full blur-3xl animate-blob"
           style={{ background: "hsl(var(--glow-3) / 0.40)", animationDelay: "12s" }} />
    </div>
  );
}
```

---

## 4. 玻璃表面（`.glass` 系列 — 本風格的靈魂）

**所有卡片 / 導覽 / 面板都用它，不要用實心 `bg-white`。** 放 `index.css` 的 `@layer components`。

```css
@layer components {
  .glass {          /* 標準卡片、導覽列 */
    @apply border border-white/40 bg-white/55 backdrop-blur-xl;
    box-shadow:
      0 8px 32px -8px hsl(220 40% 40% / 0.18),  /* 擴散柔陰影 */
      inset 0 1px 0 0 hsl(0 0% 100% / 0.6);      /* 頂緣 1px 內高光，模擬玻璃邊 */
  }
  .glass-soft {     /* 卡內次級面、表單容器、清單項 */
    @apply border border-white/30 bg-white/35 backdrop-blur-md;
    box-shadow: inset 0 1px 0 0 hsl(0 0% 100% / 0.5);
  }
  .glass-strong {   /* toast、彈出、SelectContent、需更高對比處 */
    @apply border border-white/50 bg-white/70 backdrop-blur-2xl;
    box-shadow:
      0 12px 40px -8px hsl(220 40% 40% / 0.24),
      inset 0 1px 0 0 hsl(0 0% 100% / 0.7);
  }

  /* 品牌漸層（讀 --brand-*，切主題即時生效，不要寫死 from-teal-500）*/
  .bg-brand-gradient {
    background-image: linear-gradient(to bottom right, var(--brand-from), var(--brand-to));
  }
  .bg-brand-tint {
    background-image: linear-gradient(to bottom right,
      color-mix(in srgb, var(--brand-from) 12%, transparent),
      color-mix(in srgb, var(--brand-to) 12%, transparent));
  }
  .text-gradient {
    background-image: linear-gradient(120deg, var(--brand-from), var(--brand-to));
    @apply bg-clip-text text-transparent;
  }

  /* 細捲軸 */
  .nice-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
  .nice-scroll::-webkit-scrollbar-thumb {
    background: hsl(var(--muted-foreground) / 0.25);
    border-radius: 3px;
  }
}
```

| Class | 用途 |
|---|---|
| `.glass` | 標準卡片、導覽列 |
| `.glass-soft` | 卡內次級面、表單容器、清單項 |
| `.glass-strong` | toast、彈出、SelectContent、更高對比處 |
| `.bg-brand-gradient` | 主 CTA、品牌圖示方塊、項目符號小圓點 |
| `.text-gradient` | 頁面主標題關鍵詞、Logo 文字 |
| `.nice-scroll` | 可捲動區細捲軸 |

---

## 5. Tailwind Config（`tailwind.config.js`）

```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
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
        lg: "var(--radius)",                 // 1rem  ≈ 16px
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        blob: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%":      { transform: "translate(30px, -20px) scale(1.08)" },
          "66%":      { transform: "translate(-20px, 20px) scale(0.95)" },
        },
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        blob: "blob 18s ease-in-out infinite",
        "fade-up": "fade-up 0.5s ease-out both",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
```

**圓角規則（全站一致，整體偏大圓角）：**
- 卡片 / 大容器 → `rounded-3xl`（~24px）
- 大按鈕 → `rounded-2xl`
- 按鈕 / 輸入 / select → `rounded-xl`
- badge / 圓點 → `rounded-full`
- **不用銳角小圓角（< 12px）**

---

## 6. 圓角、間距、字體

- **間距**：卡片內距 `p-6`；表單欄位群 `space-y-4`；label 與控件 `space-y-1.5`；頁面區塊 `space-y-6`；主內容置中 `max-w-3xl mx-auto`。
- **字體**：系統無襯線優先，含繁中 fallback（見 §3.1 `font-family`）。
- **標題**：主標 `text-3xl~4xl font-bold tracking-tight`，關鍵詞包 `.text-gradient`；卡片標題 `text-lg font-semibold`。
- **說明文字**：`text-sm text-muted-foreground`。

---

## 7. 版面結構

```
<GlassBackground/>                                  // fixed 背景光暈，掛最外層
<div class="flex h-screen overflow-hidden">         // 整頁不捲動
  <Sidebar/>                                        // 左：玻璃白、可折疊/可拖曳寬
  <div class="flex flex-1 flex-col min-w-0">
    <Header/>                                        // 上：h-14 玻璃白
    <main class="flex-1 overflow-auto p-6 nice-scroll">
      <div class="max-w-3xl mx-auto space-y-6">…</div>
    </main>
  </div>
</div>
```

重點：**外層 `h-screen overflow-hidden`，只有 `main` 捲動**；側邊欄與 Header 固定。

### 7.1 側邊欄（Sidebar）
- **玻璃白底**（`.glass`）＋右側 1px border。
- **寬度可手動拖曳**：預設 `240px`，範圍 `180–480`，存 `localStorage`（key 如 `xxx-sidebar-w`）。
  - 拖曳感應區：疊在右緣的隱形直條（`absolute right-0 w-[5px] h-full cursor-col-resize`，背景透明），**hover / 拖曳中才變主色**（`hsl(var(--primary)/.4)`）；拖曳時 `body { user-select:none }`。
- **可折疊**：展開＝記憶寬度；折疊＝固定 `64px`（只剩 icon、置中）。折疊鈕放 Header 左側，用方向 icon `PanelLeftClose` / `PanelLeftOpen`（lucide）。
- 內容：頂部品牌區（`h-14`，品牌方塊 `h-9 w-9 rounded-xl .bg-brand-gradient text-white`）＋分區小標＋導覽項。
- **導覽 active**：白底 `bg-white text-primary shadow-sm`；非 active：`text-muted-foreground hover:bg-white/50`。icon `18px`。

### 7.2 Header
- `h-14`、玻璃白（`.glass`）、下緣 1px border。
- 左：側邊欄折疊鈕。中/左：**頁面標題 + 副標題**（副標 `text-muted-foreground` 小字）。右：角色 chip、登出 icon 鈕。

---

## 8. 核心 UI 元件配方（shadcn 風格，直接複製到 `src/components/ui/`）

### 8.1 Button — cva，含 `gradient` 主 CTA variant

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium transition-all active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4",
  {
    variants: {
      variant: {
        gradient:    "bg-brand-gradient text-white shadow-lg shadow-primary/25 hover:brightness-105",  // 主要 CTA
        default:     "bg-primary text-primary-foreground shadow-primary/25 hover:bg-primary/90",
        secondary:   "glass-soft text-foreground hover:bg-white/50",
        outline:     "border border-input bg-white/40 backdrop-blur hover:bg-white/60",
        ghost:       "hover:bg-white/50",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        link:        "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-lg px-3",
        lg: "h-12 rounded-2xl px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);
```

### 8.2 Card — `.glass rounded-3xl`

```tsx
const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("glass rounded-3xl", className)} {...props} />
  )
);
// CardHeader: "flex flex-col space-y-1.5 p-6"
// CardTitle:  "text-lg font-semibold leading-none tracking-tight"
// CardDescription: "text-sm text-muted-foreground"
// CardContent: "p-6 pt-0"
```

需要浮起感的卡片加 hover 微動：`transition-transform hover:-translate-y-0.5`。

### 8.3 Input / Textarea / SelectTrigger — 半透明白 + 大圓角

```tsx
"flex h-10 w-full rounded-xl border border-input bg-white/50 backdrop-blur px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
```

### 8.4 SelectContent / Popover / Toast — `.glass-strong`

彈出層一律 `.glass-strong`（`bg-white/70 backdrop-blur-2xl`），確保浮在背景光暈上仍清楚。

### 8.5 Badge — 圓角膠囊，品牌色票

```tsx
const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary/10 text-primary",
        teal:    "border-transparent bg-teal-500/15 text-teal-700",
        indigo:  "border-transparent bg-indigo-500/15 text-indigo-700",
        muted:   "border-transparent bg-muted text-muted-foreground",
        outline: "text-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);
```

- **品牌圖示方塊**：`h-9 w-9 rounded-xl .bg-brand-gradient text-white`。
- **項目符號**：小圓點 `h-1.5 w-1.5 rounded-full .bg-brand-gradient`。

---

## 9. Icon 規範（lucide-react）

- **唯一 icon 來源**：`lucide-react`，線條 `strokeWidth={1.75}`，不混用其他 icon 庫。
- **尺寸慣例**：內文/按鈕 `h-4 w-4`（Button 內自動 `size-4`）；標題/區塊 `h-5 w-5`；品牌方塊圖示白色。
- **顏色**：強調 `text-primary`；一般 `text-foreground/70`；危險 `text-destructive`。
- **Loading**：一律 `<Loader2 className="animate-spin" />`。
- 常用：`Sparkles`/`Wand2`(AI) `Settings2`/`Palette`(設定·主題) `UploadCloud`/`FileText` `Copy`/`Check`/`Download` `Plus`/`Pencil`/`Trash2`/`Save` `ChevronDown` `PanelLeftClose`/`Open`。

---

## 10. 動態 / 互動慣例

- 克制、緩慢、只用於進場與背景：
  - `animate-blob`（18s，背景光暈）、`animate-fade-up`（0.5s，卡片/區塊進場）。
- 互動微回饋：按鈕 `active:scale-[0.98]` + `transition-all`；hover 提高白底透明度或亮度。
- **Toast**：用 `sonner`，成功綠、錯誤紅，右下角。
- **危險操作二次確認**：刪除重要資料用「輸入 `DELETE` 才可確認」的對話框。
- **多秒操作進度**：底部中央非阻擋小卡（`Loader2` 轉圈 + 步驟文字），完成再跳結果框；避免只用會閃掉的 toast。
- focus 統一：`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring`。
- disabled 統一：`disabled:pointer-events-none disabled:opacity-50`。

---

## 11. 可切換主題盤（Theme Variants）

玻璃結構（`.glass`、圓角、動畫、留白）**維持不變**，切換時只覆寫這幾個變數：
`--primary`、`--ring`、`--accent`、`--brand-from` / `--brand-to`（品牌漸層）、`--glow-1/2/3`（blob）、`--bg-a/b/c/d`（body 背景）。

**實作方式**：在 `<html data-theme="...">` 上切換；`index.css` 用 `[data-theme="id"] { --brand-from: ...; ... }` 覆寫變數。所有品牌漸層一律用 `.bg-brand-gradient` / `.bg-brand-tint` / `.text-gradient`（讀 `--brand-*`），blob 讀 `--glow-*`，body 讀 `--bg-*`，換一個 `data-theme` 全站配色即時變化。主題清單建議放 `src/lib/themes.ts`。

```css
/* index.css 範例：新增一套主題只要加一個區塊 */
[data-theme="sunset-coral"] {
  --primary: 16 90% 62%;  --ring: 16 90% 62%;  --accent: 32 90% 82%;
  --brand-from: #FB7185;  --brand-to: #F59E0B;
  --glow-1: 16 90% 72%;   --glow-2: 32 90% 72%;  --glow-3: 350 90% 78%;
  --bg-a: 16 90% 94%;     --bg-b: 32 90% 94%;    --bg-c: 20 60% 98%; --bg-d: 350 55% 97%;
}
```

已內建的主題盤（皆淺色）：

| 主題 | 中文 | 品牌漸層（起→迄）| 氣質 |
|---|---|---|---|
| **Aurora Glass**（預設）| 極光琉璃 | `#14B8A6 → #6366F1` | 清新、科技、通透 |
| **Sunset Coral** | 珊瑚晚霞 | `#FB7185 → #F59E0B` | 溫暖、活潑 |
| **Rose Quartz** | 玫瑰石英 | `#F472B6 → #A855F7` | 柔美、時尚 |
| **Mint Meadow** | 薄荷草原 | `#34D399 → #06B6D4` | 自然、清爽 |
| **Lavender Mist** | 薰衣草霧 | `#818CF8 → #C084FC` | 優雅、寧靜 |
| **Ocean Deep** | 深海潮 | `#3B82F6 → #22D3EE` | 沉穩、專業 |
| **Golden Hour** | 蜜金時光 | `#FBBF24 → #FB7185` | 明亮、溫馨 |
| **Graphite Frost** | 石墨霜 | `#64748B → #94A3B8` | 極簡、低調 |

> **暗色（Midnight Glass）尚未做**：目前玻璃填色寫死白色半透明（`bg-white/xx`），淺色共用沒問題，暗色底會讓對比失效。要做暗色需先把「表面填色」抽成變數（`--surface`/`--field`/`--hairline`），讓 `.glass` 系列與 input/select 改讀變數，暗色主題再覆寫成深色半透明。這是一次性重構。

---

## 12. 該做 / 不該做

**Do**
- 表面一律毛玻璃（`.glass*`），透出背景光暈。
- 重點用 teal→indigo 漸層（走 `.bg-brand-gradient` 變數）；大圓角；柔陰影；充足留白。
- 淺色、低飽和、冷色調為主。
- 進場 `fade-up`，loading 用旋轉圖示。

**Don't**
- 不用不透明實心卡片、純黑邊、生硬深陰影。
- 不用高飽和 / 暗色背景蓋掉玻璃感。
- 不用銳角小圓角（< 12px）。
- 不寫死 `from-teal-500 to-indigo-500`（改用 `.bg-brand-gradient`，否則換主題失效）。
- 動畫不要過多過快。

---

## 13. 給新 session 的「照做」清單

1. 建 Vite + React + TS 專案，裝 §1 依賴。
2. 貼上 §2.1 `:root` tokens、§3.1 `body` 背景、§4 `.glass` 系列 utilities 到 `src/index.css`；設定 §5 `tailwind.config.js`。
3. 建 `src/lib/utils.ts` 的 `cn()`（§1）。
4. 建 `components/GlassBackground.tsx`（§3.2），掛在最外層。
5. 從 §8 複製 `ui/`：`button`（含 `gradient` variant）`card`（`.glass rounded-3xl`）`input / select / badge / ...`。
6. 版面照 §7：`GlassBackground` + `h-screen overflow-hidden` + 只有 `main` 捲動 + 可拖曳折疊 Sidebar + `h-14` Header。
7. 若要主題切換，照 §11 用 `[data-theme]` 覆寫變數 + `themes.ts`。
8. 全程遵守：**表面用 `.glass`、重點用 `.bg-brand-gradient`（不寫死）、大圓角照 §5、icon 用 lucide 加 `strokeWidth={1.75}`、進場 `fade-up`、彈出層用 `.glass-strong`。**

> 一句判準：畫面看起來像「淡藍紫漸層 + 飄移光暈背景，前景是半透明玻璃白的側邊欄 / Header / 卡片；主色 indigo、teal→indigo 漸層點綴、大圓角、線條 icon、細捲軸；只有主內容區捲動；清爽、通透、專業」就對了。
