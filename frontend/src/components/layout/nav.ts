import { GraduationCap, Library, Settings2, Workflow, type LucideIcon } from "lucide-react";

export type NavItem = { to: string; label: string; icon: LucideIcon; end?: boolean };

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "導師", icon: GraduationCap, end: true },
  { to: "/library", label: "靈感庫", icon: Library },
  { to: "/mindmap", label: "心智圖", icon: Workflow },
  { to: "/settings", label: "設定", icon: Settings2 },
];
