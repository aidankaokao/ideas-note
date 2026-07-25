import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Loader2, Search } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Note, Topic } from "@/lib/types";
import { cn } from "@/lib/utils";
import { usePageHeader } from "@/stores/pageHeader";

const PAGE_SIZE = 5;

function SourceBadge({ source }: { source: string }) {
  if (source === "agent-extend") return <Badge variant="teal">AI 延伸</Badge>;
  if (source === "qa-extract") return <Badge variant="indigo">問答萃取</Badge>;
  if (source === "assistant") return <Badge>導師建立</Badge>;
  return null;
}

export default function LibraryPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [topicId, setTopicId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    usePageHeader.getState().set("靈感庫", "翻找與查詢你的所有靈感");
    api
      .get<Note[]>("/notes")
      .then(setNotes)
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
    api.get<Topic[]>("/topics").then(setTopics).catch(() => {});
  }, []);

  const topicNoteIds = useMemo(() => {
    if (topicId === null) return null;
    const topic = topics.find((t) => t.id === topicId);
    return topic ? new Set(topic.notes.map((n) => n.id)) : null;
  }, [topicId, topics]);

  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase();
    return notes.filter((n) => {
      if (topicNoteIds && !topicNoteIds.has(n.id)) return false;
      if (kw && !n.title.toLowerCase().includes(kw) && !n.content.toLowerCase().includes(kw)) return false;
      return true;
    });
  }, [notes, q, topicNoteIds]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pageCount);
  const shown = filtered.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);

  const selectTopic = (id: number | null) => {
    setTopicId(id);
    setPage(1);
  };

  return (
    <>
      {/* 搜尋 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
        <Input
          placeholder="搜尋靈感…"
          className="pl-9"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {/* 主題篩選（來自導師整理的知識體系） */}
      {topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => selectTopic(null)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs transition-colors",
              topicId === null
                ? "border-transparent bg-brand-gradient text-white"
                : "border-input bg-white/40 backdrop-blur hover:bg-white/60"
            )}
          >
            全部
          </button>
          {topics.map((t) => (
            <button
              key={t.id}
              onClick={() => selectTopic(t.id)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                topicId === t.id
                  ? "border-transparent bg-brand-gradient text-white"
                  : "border-input bg-white/40 backdrop-blur hover:bg-white/60"
              )}
            >
              {t.name}（{t.notes.length}）
            </button>
          ))}
        </div>
      )}

      {/* 清單 */}
      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" strokeWidth={1.75} />
        </div>
      ) : shown.length === 0 ? (
        <Card className="p-10 text-center text-sm text-muted-foreground animate-fade-up">
          {q || topicId !== null ? "找不到符合的靈感" : "還沒有靈感——到「靈感導師」頁記下第一個吧！"}
        </Card>
      ) : (
        <div className="space-y-3">
          {shown.map((n) => (
            <Card
              key={n.id}
              className="cursor-pointer p-5 transition-transform hover:-translate-y-0.5 animate-fade-up"
              onClick={() => navigate(`/notes/${n.id}`)}
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold">{n.title}</h3>
                <SourceBadge source={n.source} />
              </div>
              {n.content && (
                <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground line-clamp-3">{n.content}</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground/70">
                {new Date(n.updated_at).toLocaleString("zh-TW", { dateStyle: "medium", timeStyle: "short" })}
              </p>
            </Card>
          ))}
        </div>
      )}

      {/* 分頁：每頁 5 筆 */}
      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="outline" size="icon" disabled={current <= 1} onClick={() => setPage(current - 1)}>
            <ChevronLeft strokeWidth={1.75} />
          </Button>
          <span className="text-sm text-muted-foreground">
            第 {current} / {pageCount} 頁（共 {filtered.length} 筆）
          </span>
          <Button variant="outline" size="icon" disabled={current >= pageCount} onClick={() => setPage(current + 1)}>
            <ChevronRight strokeWidth={1.75} />
          </Button>
        </div>
      )}
    </>
  );
}
