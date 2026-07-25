import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, GraduationCap, Loader2, Save, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import { MentorChat } from "@/components/MentorChat";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Note, NoteLink } from "@/lib/types";
import { usePageHeader } from "@/stores/pageHeader";

const NOTE_PRESETS = [
  "延伸這則靈感",
  "找相關的靈感，建議怎麼結合",
  "根據我們的討論，幫我修改這則靈感",
];

export default function NoteDetailPage() {
  const { id } = useParams();
  const noteId = Number(id);
  const navigate = useNavigate();

  const [note, setNote] = useState<Note | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [links, setLinks] = useState<NoteLink[]>([]);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const loadLinks = useCallback(() => {
    api.get<NoteLink[]>(`/notes/${noteId}/links`).then(setLinks).catch(() => {});
  }, [noteId]);

  useEffect(() => {
    usePageHeader.getState().set("靈感詳情", "編輯，或找導師聊聊這則靈感");
    api
      .get<Note>(`/notes/${noteId}`)
      .then((n) => {
        setNote(n);
        setTitle(n.title);
        setContent(n.content);
      })
      .catch((e) => {
        toast.error((e as Error).message);
        navigate("/library");
      });
    loadLinks();
    setChatOpen(false);
  }, [noteId, navigate, loadLinks]);

  const save = async () => {
    if (saving) return;
    setSaving(true);
    try {
      const updated = await api.put<Note>(`/notes/${noteId}`, { title, content });
      setNote(updated);
      setTitle(updated.title);
      toast.success("已儲存");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    try {
      await api.del(`/notes/${noteId}`);
      toast.success("已刪除");
      navigate("/library");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const removeLink = async (linkId: number) => {
    try {
      await api.del(`/notes/links/${linkId}`);
      setLinks((prev) => prev.filter((l) => l.id !== linkId));
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  // 導師套用修改提案後，同步畫面
  const onNoteUpdated = (updated: Note) => {
    if (updated.id !== noteId) return;
    setNote(updated);
    setTitle(updated.title);
    setContent(updated.content);
    loadLinks();
  };

  if (!note) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-primary" strokeWidth={1.75} />
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft strokeWidth={1.75} /> 返回
        </Button>
        <div className="flex gap-2">
          <Button variant="destructive" size="sm" onClick={() => setConfirmDelete(true)}>
            <Trash2 strokeWidth={1.75} /> 刪除
          </Button>
          <Button variant="gradient" size="sm" onClick={save} disabled={saving}>
            {saving ? <Loader2 className="animate-spin" /> : <Save strokeWidth={1.75} />} 儲存
          </Button>
        </div>
      </div>

      {/* 編輯 */}
      <Card className="p-6 animate-fade-up">
        <Input
          className="border-none bg-transparent px-0 text-lg font-semibold focus-visible:ring-0"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="標題"
        />
        <Textarea
          rows={10}
          className="mt-2"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="靈感內容…"
        />
      </Card>

      {/* 既有連結 */}
      {links.length > 0 && (
        <Card className="animate-fade-up">
          <CardHeader>
            <CardTitle>連結的靈感</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {links.map((l) => (
              <div key={l.id} className="glass-soft flex items-center gap-2 rounded-2xl px-4 py-2.5">
                <Badge variant={l.direction === "out" ? "teal" : "indigo"}>
                  {l.direction === "out" ? "連往" : "來自"}
                </Badge>
                <Link
                  to={`/notes/${l.other_note_id}`}
                  className="min-w-0 flex-1 truncate text-sm font-medium hover:text-primary"
                  title={l.reason}
                >
                  {l.other_title}
                </Link>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => removeLink(l.id)}>
                  <X className="!size-3.5" strokeWidth={1.75} />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 懸浮導師按鈕 */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          title="找導師聊這則靈感"
          className="fixed bottom-20 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-brand-gradient text-white shadow-lg shadow-primary/30 transition-transform hover:scale-105 active:scale-95 md:bottom-8 md:right-8"
        >
          <GraduationCap className="h-6 w-6" strokeWidth={1.75} />
        </button>
      )}

      {/* 聚焦此筆記的導師對話（手機全版、桌機右側欄） */}
      {chatOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-sm" onClick={() => setChatOpen(false)}>
          <div
            className="glass-strong flex h-full w-full flex-col p-4 sm:w-[28rem] sm:rounded-l-3xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white">
                <GraduationCap className="h-4 w-4" strokeWidth={1.75} />
              </div>
              <span className="min-w-0 flex-1 truncate text-sm font-semibold">聊聊：{note.title}</span>
              <Button variant="ghost" size="icon" onClick={() => setChatOpen(false)}>
                <X strokeWidth={1.75} />
              </Button>
            </div>
            <div className="min-h-0 flex-1">
              <MentorChat noteId={noteId} presetSuggestions={NOTE_PRESETS} onNoteUpdated={onNoteUpdated} fill />
            </div>
          </div>
        </div>
      )}

      {/* 刪除確認 */}
      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} title="刪除這篇靈感？">
        <p className="text-sm text-muted-foreground">「{note.title}」與它的連結都會被刪除，無法復原。</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setConfirmDelete(false)}>取消</Button>
          <Button variant="destructive" onClick={remove}>確認刪除</Button>
        </div>
      </Dialog>
    </>
  );
}
