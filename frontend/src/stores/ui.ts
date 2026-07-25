import { create } from "zustand";

type UIState = {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
};

export const useUI = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
