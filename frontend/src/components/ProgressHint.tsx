import { Loader2 } from "lucide-react";

/** 多秒操作進度：底部中央非阻擋小卡（Aurora Glass §10）。 */
export function ProgressHint({ text }: { text: string }) {
  return (
    <div className="fixed bottom-20 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-2xl px-4 py-3 text-sm glass-strong animate-fade-up md:bottom-6">
      <Loader2 className="h-4 w-4 animate-spin text-primary" strokeWidth={1.75} />
      {text}
    </div>
  );
}
