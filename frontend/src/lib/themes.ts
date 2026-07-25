// 主題盤（Aurora Glass §11）：切 data-theme 覆寫 CSS 變數，玻璃結構不變。
export type Theme = { id: string; name: string; from: string; to: string };

export const THEMES: Theme[] = [
  { id: "aurora-glass",   name: "極光琉璃", from: "#14B8A6", to: "#6366F1" },
  { id: "sunset-coral",   name: "珊瑚晚霞", from: "#FB7185", to: "#F59E0B" },
  { id: "rose-quartz",    name: "玫瑰石英", from: "#F472B6", to: "#A855F7" },
  { id: "mint-meadow",    name: "薄荷草原", from: "#34D399", to: "#06B6D4" },
  { id: "lavender-mist",  name: "薰衣草霧", from: "#818CF8", to: "#C084FC" },
  { id: "ocean-deep",     name: "深海潮",   from: "#3B82F6", to: "#22D3EE" },
  { id: "golden-hour",    name: "蜜金時光", from: "#FBBF24", to: "#FB7185" },
  { id: "graphite-frost", name: "石墨霜",   from: "#64748B", to: "#94A3B8" },
];

const STORAGE_KEY = "ideas-note-theme";

export function applyTheme(id: string) {
  if (id === "aurora-glass") {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", id);
  }
  localStorage.setItem(STORAGE_KEY, id);
}

export function currentTheme(): string {
  return localStorage.getItem(STORAGE_KEY) ?? "aurora-glass";
}

export function initTheme() {
  applyTheme(currentTheme());
}
