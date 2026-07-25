import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type DialogProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
};

/** 彈出層一律 .glass-strong（Aurora Glass §8.4）；手機貼底、桌機置中。 */
export function Dialog({ open, onClose, title, children, className }: DialogProps) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/20 p-4 backdrop-blur-sm sm:items-center"
      onClick={onClose}
    >
      <div
        className={cn(
          "glass-strong w-full max-w-md rounded-3xl p-6 animate-fade-up max-h-[85vh] overflow-auto nice-scroll",
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {title && <h3 className="mb-4 text-lg font-semibold">{title}</h3>}
        {children}
      </div>
    </div>
  );
}
