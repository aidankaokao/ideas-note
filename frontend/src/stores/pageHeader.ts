import { create } from "zustand";

type State = {
  title: string;
  subtitle?: string;
  set: (title: string, subtitle?: string) => void;
};

export const usePageHeader = create<State>((set) => ({
  title: "",
  set: (title, subtitle) => set({ title, subtitle }),
}));
