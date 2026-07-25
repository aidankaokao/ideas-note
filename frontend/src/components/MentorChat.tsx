import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Check,
  Eraser,
  Gauge,
  GraduationCap,
  Library,
  Loader2,
  NotebookPen,
  PenLine,
  Send,
  Sparkles,
  Trash2,
  Workflow,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

import { ProgressHint } from "@/components/ProgressHint";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Briefing, ChatMessage, MentorAction, MentorContext, Note } from "@/lib/types";
import { cn } from "@/lib/utils";

type Props = {
  noteId?: number;                 // 有值＝聚焦單篇筆記的對話（thread 各自獨立）
  presetSuggestions?: string[];    // 輸入框上方常駐的快捷指令
  onNoteUpdated?: (note: Note) => void; // 套用修改提案後回呼（筆記頁同步畫面）
  fill?: boolean;                  // true＝填滿容器：訊息內部捲動、輸入框固定在底部
};

export function MentorChat({ noteId, presetSuggestions, onNoteUpdated, fill }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [context, setContext] = useState<MentorContext | null>(null);
  const [contextOpen, setContextOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [savingNote, setSavingNote] = useState(false);
  const [inputHidden, setInputHidden] = useState(false); // 手機版收合輸入區
  const bottomRef = useRef<HTMLDivElement>(null);

  // 觸控裝置（手機/平板）：Enter 只換行，送出一律按「問答」鈕
  const isTouch = useRef(
    typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches
  ).current;

  const qs = noteId ? `?note_id=${noteId}` : "";

  // 畫面每次打開都是乾淨的（不載入歷史）；長期記憶存在後端 DB，導師仍記得先前對話。
  useEffect(() => {
    api.get<MentorContext>(`/agent/mentor/context${qs}`).then(setContext).catch(() => {});
    if (!noteId) {
      api.get<Briefing>("/agent/mentor/briefing").then(setBriefing).catch(() => {});
    }
  }, [qs, noteId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  const send = useCallback(
    async (text?: string) => {
      const message = (text ?? input).trim();
      if (!message || busy) return;
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      if (!text) setInput("");
      setBusy(true);
      let started = false; // 是否已建立串流中的 assistant 訊息
      let errMsg: string | null = null;
      try {
        await api.stream("/agent/mentor/stream", { message, note_id: noteId ?? null }, (ev) => {
          if (ev.type === "token") {
            const t = ev.text as string;
            if (!started) {
              started = true;
              setMessages((prev) => [...prev, { role: "assistant", content: t }]);
            } else {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                next[next.length - 1] = { ...last, content: last.content + t };
                return next;
              });
            }
          } else if (ev.type === "done") {
            const final: ChatMessage = {
              role: "assistant",
              content: ev.reply as string,
              payload: {
                suggestions: ev.suggestions as string[],
                actions: ev.actions as MentorAction[],
              },
            };
            setMessages((prev) => {
              const next = [...prev];
              if (started) next[next.length - 1] = final;
              else next.push(final);
              return next;
            });
            setContext(ev.context as MentorContext);
          } else if (ev.type === "error") {
            errMsg = ev.message as string;
          }
        });
        if (errMsg) toast.error(errMsg);
      } catch (e) {
        toast.error((e as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [input, busy, noteId]
  );

  const saveAsNote = async () => {
    const content = input.trim();
    if (!content || savingNote) return;
    setSavingNote(true);
    try {
      const note = await api.post<Note>("/notes", { content });
      setInput("");
      toast.success(
        <span>
          已記下靈感：<Link className="underline" to={`/notes/${note.id}`}>{note.title}</Link>
        </span>
      );
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingNote(false);
    }
  };

  const applyProposal = async (a: Extract<MentorAction, { type: "note_update_proposal" }>) => {
    try {
      const updated = await api.put<Note>(`/notes/${a.note_id}`, {
        title: a.new_title,
        content: a.new_content,
      });
      toast.success("已套用修改");
      onNoteUpdated?.(updated);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  /** 只清畫面（本次 session）；導師的長期記憶（DB）不動。 */
  const clearScreen = () => setMessages([]);

  /** 清除長期記憶：刪掉後端這個 thread 的全部對話與壓縮摘要。 */
  const wipeMemory = async () => {
    if (!window.confirm("清除導師的長期記憶（含壓縮摘要）？此動作無法復原，筆記本身不受影響。")) return;
    try {
      await api.del(`/agent/mentor/history${qs}`);
      setMessages([]);
      const fresh = await api.get<MentorContext>(`/agent/mentor/context${qs}`);
      setContext(fresh);
      setContextOpen(false);
      toast.success("已清除長期記憶");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const renderAction = (a: MentorAction, key: number) => {
    switch (a.type) {
      case "note_created":
        return (
          <Link key={key} to={`/notes/${a.note_id}`} className="glass-soft flex items-center gap-2 rounded-2xl px-4 py-2.5 hover:bg-white/50">
            <Sparkles className="h-4 w-4 shrink-0 text-primary" strokeWidth={1.75} />
            <span className="text-sm">已建立靈感：<span className="font-medium">{a.title}</span></span>
          </Link>
        );
      case "note_update_proposal":
        return (
          <div key={key} className="glass-soft space-y-2 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <NotebookPen className="h-4 w-4 text-primary" strokeWidth={1.75} />
              修改提案：{a.old_title}
            </div>
            {a.reason && <p className="text-xs text-muted-foreground">{a.reason}</p>}
            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-sm font-medium">{a.new_title}</p>
              <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground line-clamp-6">{a.new_content}</p>
            </div>
            <div className="flex justify-end gap-2">
              <Link to={`/notes/${a.note_id}`}>
                <Button variant="outline" size="sm">看原文</Button>
              </Link>
              <Button variant="gradient" size="sm" onClick={() => applyProposal(a)}>
                <Check strokeWidth={1.75} /> 套用
              </Button>
            </div>
          </div>
        );
      case "mindmap_saved":
        return (
          <Link key={key} to={`/mindmap?id=${a.id}`} className="glass-soft flex items-center gap-2 rounded-2xl px-4 py-2.5 hover:bg-white/50">
            <Workflow className="h-4 w-4 shrink-0 text-primary" strokeWidth={1.75} />
            <span className="text-sm">心智圖已保存：<span className="font-medium">{a.title}</span>（點擊查看）</span>
          </Link>
        );
      case "topics_updated":
        return (
          <div key={key} className="glass-soft space-y-2 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Library className="h-4 w-4 text-primary" strokeWidth={1.75} /> 知識體系已更新
            </div>
            <div className="flex flex-wrap gap-1.5">
              {a.topics.map((t, i) => (
                <Badge key={i} variant="muted">{t.name}（{t.count}）</Badge>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">可到「靈感庫」用主題篩選翻找。</p>
          </div>
        );
      default:
        return null;
    }
  };

  const suggestionChip = (s: string, key: number) => (
    <button
      key={key}
      onClick={() => send(s)}
      disabled={busy}
      className="rounded-full border border-input bg-white/40 px-3 py-1 text-xs backdrop-blur transition-colors hover:bg-white/60 disabled:opacity-50"
    >
      {s}
    </button>
  );

  return (
    <div className={cn("flex flex-col gap-4", fill && "h-full min-h-0")}>
      {/* 訊息區（fill 模式內部捲動，輸入框不會被推走） */}
      <div className={cn("space-y-4", fill && "min-h-0 flex-1 overflow-y-auto nice-scroll pr-1")}>
        {/* 每日簡報（僅主頁對話） */}
        {!noteId && briefing && (
          <Card className="p-5 animate-fade-up">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white">
                <GraduationCap className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm">{briefing.greeting}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {briefing.suggestions.map(suggestionChip)}
                </div>
              </div>
            </div>
          </Card>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-brand-gradient px-4 py-2.5 text-sm text-white shadow-lg shadow-primary/25">
                {m.content}
              </div>
            </div>
          ) : (
            <Card key={i} className="p-5 animate-fade-up">
              <div className="markdown">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
              {m.payload?.actions && m.payload.actions.length > 0 && (
                <div className="mt-3 space-y-2">{m.payload.actions.map(renderAction)}</div>
              )}
              {m.payload?.suggestions && m.payload.suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {m.payload.suggestions.map(suggestionChip)}
                </div>
              )}
            </Card>
          )
        )}
        <div ref={bottomRef} />
      </div>

      {/* 輸入區（手機可收合成懸浮鈕；桌機恆顯示） */}
      <Card className={cn("relative shrink-0 p-4", inputHidden && "hidden md:block")}>
        {/* 手機版收合鈕（僅主頁） */}
        {!noteId && (
          <button
            onClick={() => setInputHidden(true)}
            title="收合輸入區"
            className="absolute -top-2.5 right-3 flex h-6 w-6 items-center justify-center rounded-full glass-strong text-muted-foreground md:hidden"
          >
            <X className="h-3.5 w-3.5" strokeWidth={1.75} />
          </button>
        )}
        {presetSuggestions && presetSuggestions.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {presetSuggestions.map(suggestionChip)}
          </div>
        )}
        <Textarea
          rows={2}
          placeholder={noteId ? "跟導師聊聊這則靈感…" : "記下靈感，或問導師任何事…"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            // 觸控裝置：Enter 一律換行，送出靠「問答」鈕
            if (isTouch) return;
            // 注音/日文等輸入法組字中按 Enter 是「選字」，不能送出（isComposing / keyCode 229）
            if (e.nativeEvent.isComposing || e.keyCode === 229) return;
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <div className="mt-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            {context && (
              <Button
                variant="ghost"
                size="sm"
                className="px-2 text-muted-foreground"
                onClick={() => setContextOpen(true)}
                title="查看記憶上下文用量"
              >
                <Gauge strokeWidth={1.75} /> 記憶 {context.percent}%
              </Button>
            )}
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="px-2 text-muted-foreground"
                onClick={clearScreen}
                title="只清除畫面，導師的長期記憶不受影響"
              >
                <Eraser strokeWidth={1.75} /> 清空畫面
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={saveAsNote} disabled={!input.trim() || savingNote}>
              {savingNote ? <Loader2 className="animate-spin" /> : <NotebookPen strokeWidth={1.75} />}
              記筆記
            </Button>
            <Button variant="gradient" onClick={() => send()} disabled={!input.trim() || busy}>
              {busy ? <Loader2 className="animate-spin" /> : <Send strokeWidth={1.75} />}
              問答
            </Button>
          </div>
        </div>
      </Card>

      {/* 手機版：輸入區收合後的展開懸浮鈕 */}
      {!noteId && inputHidden && (
        <button
          onClick={() => setInputHidden(false)}
          title="展開輸入區"
          className="fixed bottom-20 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-brand-gradient text-white shadow-lg shadow-primary/30 transition-transform hover:scale-105 active:scale-95 md:hidden"
        >
          <PenLine className="h-5 w-5" strokeWidth={1.75} />
        </button>
      )}

      {/* 長期記憶詳情 */}
      <Dialog open={contextOpen} onClose={() => setContextOpen(false)} title="導師的長期記憶">
        {context && (
          <div className="space-y-4">
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span>已使用 {context.percent}%</span>
                <span className="text-muted-foreground">
                  約 {context.used} / {context.budget} 字
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-brand-gradient transition-all"
                  style={{ width: `${Math.min(100, context.percent)}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                ＝壓縮摘要 {context.summary.length} 字＋近期對話 {Math.max(0, context.used - context.summary.length)} 字
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              記憶存在資料庫、跨裝置共用：「清空畫面」不會影響它。超過 80% 會自動把較舊的對話壓縮成摘要，
              所以壓縮後百分比會下降但不會歸零——摘要本身就是留下來的長期記憶。
            </p>
            {context.summary ? (
              <div>
                <h4 className="mb-1 text-sm font-semibold">已壓縮的對話摘要</h4>
                <div className="glass-soft max-h-48 overflow-auto whitespace-pre-wrap rounded-2xl p-3 text-xs text-muted-foreground nice-scroll">
                  {context.summary}
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">目前還沒有壓縮過的摘要。</p>
            )}
            <div className="flex justify-end">
              <Button variant="destructive" size="sm" onClick={wipeMemory}>
                <Trash2 strokeWidth={1.75} /> 清除長期記憶
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {busy && <ProgressHint text="導師正在查閱你的靈感並思考…" />}
    </div>
  );
}
