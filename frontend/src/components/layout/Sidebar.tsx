import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { Sparkles } from "lucide-react";

import { NAV_ITEMS } from "@/components/layout/nav";
import { useUI } from "@/stores/ui";
import { cn } from "@/lib/utils";

const WIDTH_KEY = "ideas-note-sidebar-w";

/** 桌機側邊欄（Aurora Glass §7.1）：玻璃白、可折疊、可拖曳寬；手機隱藏（改底部導覽）。 */
export function Sidebar() {
  const collapsed = useUI((s) => s.sidebarCollapsed);
  const [width, setWidth] = useState(() => {
    const saved = Number(localStorage.getItem(WIDTH_KEY));
    return saved >= 180 && saved <= 480 ? saved : 240;
  });
  const dragging = useRef(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const w = Math.min(480, Math.max(180, e.clientX));
      setWidth(w);
      localStorage.setItem(WIDTH_KEY, String(w));
    };
    const onUp = () => {
      dragging.current = false;
      setIsDragging(false);
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  return (
    <aside
      className="relative hidden shrink-0 flex-col border-r glass md:flex"
      style={{ width: collapsed ? 64 : width }}
    >
      {/* 品牌區 */}
      <div className={cn("flex h-14 items-center gap-2 px-3", collapsed && "justify-center px-0")}>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white">
          <Sparkles className="h-5 w-5" strokeWidth={1.75} />
        </div>
        {!collapsed && <span className="truncate text-lg font-bold text-gradient">靈感筆記</span>}
      </div>

      {/* 導覽 */}
      <nav className="flex-1 space-y-1 overflow-auto p-2 nice-scroll">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                isActive
                  ? "bg-white text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-white/50"
              )
            }
            title={label}
          >
            <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* 拖曳感應區：hover / 拖曳中才變主色 */}
      {!collapsed && (
        <div
          className={cn(
            "absolute right-0 top-0 h-full w-[5px] cursor-col-resize",
            isDragging ? "bg-primary/40" : "hover:bg-primary/40"
          )}
          onMouseDown={() => {
            dragging.current = true;
            setIsDragging(true);
            document.body.style.userSelect = "none";
          }}
        />
      )}
    </aside>
  );
}
