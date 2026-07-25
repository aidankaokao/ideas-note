import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "@/components/layout/nav";
import { cn } from "@/lib/utils";

/** 手機底部導覽列（桌機隱藏，改用 Sidebar）。 */
export function MobileNav() {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex justify-around border-t glass-strong md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-col items-center gap-0.5 px-3 py-2 text-[10px] font-medium transition-colors",
              isActive ? "text-primary" : "text-muted-foreground"
            )
          }
        >
          <Icon className="h-5 w-5" strokeWidth={1.75} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
