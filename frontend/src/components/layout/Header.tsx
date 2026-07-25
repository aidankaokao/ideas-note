import { LogOut, PanelLeftClose, PanelLeftOpen, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/stores/auth";
import { usePageHeader } from "@/stores/pageHeader";
import { useUI } from "@/stores/ui";

export function Header() {
  const { sidebarCollapsed, toggleSidebar } = useUI();
  const { title, subtitle } = usePageHeader();
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b px-4 glass">
      <Button
        variant="ghost"
        size="icon"
        className="hidden md:inline-flex"
        onClick={toggleSidebar}
        title={sidebarCollapsed ? "展開側邊欄" : "折疊側邊欄"}
      >
        {sidebarCollapsed ? <PanelLeftOpen strokeWidth={1.75} /> : <PanelLeftClose strokeWidth={1.75} />}
      </Button>

      {/* 手機：顯示品牌小方塊 */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white md:hidden">
        <Sparkles className="h-4 w-4" strokeWidth={1.75} />
      </div>

      <div className="min-w-0">
        <div className="truncate font-semibold">{title}</div>
        {subtitle && <div className="truncate text-xs text-muted-foreground">{subtitle}</div>}
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Badge variant="muted" className="max-w-[8rem] truncate">
          {user?.username}
          {user?.is_admin ? "・管理員" : ""}
        </Badge>
        <Button variant="ghost" size="icon" onClick={logout} title="登出">
          <LogOut strokeWidth={1.75} />
        </Button>
      </div>
    </header>
  );
}
