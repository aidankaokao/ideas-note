import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Download, FileText, Loader2, Pencil, RefreshCw, Trash2, Wand2, Workflow } from "lucide-react";
import { Transformer } from "markmap-lib";
import { Markmap } from "markmap-view";
import { toast } from "sonner";

import { ProgressHint } from "@/components/ProgressHint";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Mindmap, Topic } from "@/lib/types";
import { cn } from "@/lib/utils";
import { usePageHeader } from "@/stores/pageHeader";

const transformer = new Transformer();

function downloadBlob(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function MindMapPage() {
  const [params] = useSearchParams();
  const [maps, setMaps] = useState<Mindmap[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Mindmap | null>(null);
  const [scope, setScope] = useState("all");
  const [customQuery, setCustomQuery] = useState("");
  const [generating, setGenerating] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [showAllChips, setShowAllChips] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editMd, setEditMd] = useState("");
  const svgRef = useRef<SVGSVGElement>(null);

  const CHIP_LIMIT = 12;

  useEffect(() => {
    usePageHeader.getState().set("心智圖", "生成、查看與下載你的心智圖");
    api
      .get<Mindmap[]>("/mindmaps")
      .then((list) => {
        setMaps(list);
        const wanted = Number(params.get("id"));
        setSelected(wanted ? list.find((m) => m.id === wanted) ?? list[0] ?? null : list[0] ?? null);
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
    api.get<Topic[]>("/topics").then(setTopics).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const generate = async () => {
    if (generating) return;
    setGenerating(true);
    try {
      const query = customQuery.trim();
      const body = query
        ? { query }
        : scope === "all"
          ? {}
          : { topic_id: Number(scope) };
      const res = await api.post<{ id: number; note_count: number }>("/agent/mindmap", body);
      const list = await api.get<Mindmap[]>("/mindmaps");
      setMaps(list);
      setSelected(list.find((m) => m.id === res.id) ?? list[0] ?? null);
      setCustomQuery("");
      toast.success(`已根據 ${res.note_count} 篇靈感生成心智圖`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    if (!selected || !svgRef.current) return;
    svgRef.current.innerHTML = "";
    const { root } = transformer.transform(selected.markdown);
    const mm = Markmap.create(svgRef.current, { autoFit: true }, root);
    return () => mm.destroy();
  }, [selected]);

  const downloadMd = () => {
    if (!selected) return;
    downloadBlob(`${selected.title}.md`, selected.markdown, "text/markdown;charset=utf-8");
  };

  const downloadSvg = () => {
    const svg = svgRef.current;
    if (!svg || !selected) return;
    const clone = svg.cloneNode(true) as SVGSVGElement;
    const rect = svg.getBoundingClientRect();
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", String(Math.round(rect.width)));
    clone.setAttribute("height", String(Math.round(rect.height)));
    clone.style.background = "#ffffff";
    downloadBlob(`${selected.title}.svg`, clone.outerHTML, "image/svg+xml;charset=utf-8");
  };

  const regenerate = async () => {
    if (!selected || regenerating) return;
    setRegenerating(true);
    try {
      const updated = await api.post<Mindmap & { note_count: number }>(
        `/mindmaps/${selected.id}/regenerate`
      );
      setMaps((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setSelected(updated);
      toast.success(`已重新生成（取材 ${updated.note_count} 篇靈感）`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setRegenerating(false);
    }
  };

  const openEdit = () => {
    if (!selected) return;
    setEditTitle(selected.title);
    setEditMd(selected.markdown);
    setEditOpen(true);
  };

  const saveEdit = async () => {
    if (!selected) return;
    try {
      const updated = await api.put<Mindmap>(`/mindmaps/${selected.id}`, {
        title: editTitle,
        markdown: editMd,
      });
      setMaps((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setSelected(updated);
      setEditOpen(false);
      toast.success("已儲存");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const remove = async (m: Mindmap) => {
    if (!window.confirm(`刪除心智圖「${m.title}」？`)) return;
    try {
      await api.del(`/mindmaps/${m.id}`);
      const rest = maps.filter((x) => x.id !== m.id);
      setMaps(rest);
      if (selected?.id === m.id) setSelected(rest[0] ?? null);
      toast.success("已刪除");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-6 w-6 animate-spin text-primary" strokeWidth={1.75} />
      </div>
    );
  }

  return (
    <>
      {/* 生成：全部 / 某主題 / 自訂範圍描述 */}
      <Card className="p-6 animate-fade-up">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-36 flex-1 space-y-1.5">
            <label className="text-sm font-medium">範圍</label>
            <Select value={scope} onChange={(e) => setScope(e.target.value)} disabled={!!customQuery.trim()}>
              <option value="all">全部靈感</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>主題：{t.name}</option>
              ))}
            </Select>
          </div>
          <div className="min-w-48 flex-[2] space-y-1.5">
            <label className="text-sm font-medium">或自訂範圍（AI 會找相關靈感）</label>
            <Input
              placeholder="例：跟行銷有關的想法、咖啡店的營運"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
            />
          </div>
          <Button variant="gradient" onClick={generate} disabled={generating}>
            {generating ? <Loader2 className="animate-spin" /> : <Wand2 strokeWidth={1.75} />}
            生成心智圖
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          填了自訂範圍就以描述為準；生成後會自動保存到下方清單。也可以直接在「靈感導師」頁用說的。
        </p>
      </Card>

      {maps.length === 0 && (
        <Card className="p-10 text-center animate-fade-up">
          <Workflow className="mx-auto h-8 w-8 text-primary" strokeWidth={1.75} />
          <p className="mt-3 text-sm text-muted-foreground">還沒有心智圖，從上面生成第一張吧！</p>
        </Card>
      )}

      {/* 已保存清單（超過上限收合） */}
      <div className="flex flex-wrap gap-1.5">
        {(showAllChips ? maps : maps.slice(0, CHIP_LIMIT)).map((m) => (
          <button
            key={m.id}
            onClick={() => setSelected(m)}
            className={cn(
              "max-w-full truncate rounded-full border px-3 py-1 text-xs transition-colors",
              selected?.id === m.id
                ? "border-transparent bg-brand-gradient text-white"
                : "border-input bg-white/40 backdrop-blur hover:bg-white/60"
            )}
          >
            {m.title}
          </button>
        ))}
        {maps.length > CHIP_LIMIT && (
          <button
            onClick={() => setShowAllChips((v) => !v)}
            className="rounded-full border border-input bg-white/40 px-3 py-1 text-xs font-medium text-primary backdrop-blur hover:bg-white/60"
          >
            {showAllChips ? "收合" : `+${maps.length - CHIP_LIMIT} 更多`}
          </button>
        )}
      </div>

      {selected && (
        <Card className="p-4 animate-fade-up">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <h3 className="truncate font-semibold">{selected.title}</h3>
              <p className="text-xs text-muted-foreground">
                {new Date(selected.created_at).toLocaleString("zh-TW", { dateStyle: "medium", timeStyle: "short" })}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={regenerate} disabled={regenerating} title="用原本的範圍重新取材重畫">
                {regenerating ? <Loader2 className="animate-spin" /> : <RefreshCw strokeWidth={1.75} />} 重新生成
              </Button>
              <Button variant="outline" size="sm" onClick={openEdit}>
                <Pencil strokeWidth={1.75} /> 編輯
              </Button>
              <Button variant="outline" size="sm" onClick={downloadMd}>
                <FileText strokeWidth={1.75} /> Markdown
              </Button>
              <Button variant="outline" size="sm" onClick={downloadSvg}>
                <Download strokeWidth={1.75} /> SVG
              </Button>
              <Button variant="ghost" size="sm" className="text-destructive" onClick={() => remove(selected)}>
                <Trash2 strokeWidth={1.75} />
              </Button>
            </div>
          </div>
          <div className="overflow-hidden rounded-2xl bg-white/60">
            <svg ref={svgRef} className="h-[65vh] w-full" />
          </div>
        </Card>
      )}

      {/* 手動編輯（markdown 階層即心智圖結構） */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} title="編輯心智圖" className="max-w-2xl">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">標題</label>
            <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Markdown（#/##/### 標題＝階層）</label>
            <Textarea
              rows={14}
              className="font-mono text-xs"
              value={editMd}
              onChange={(e) => setEditMd(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditOpen(false)}>取消</Button>
            <Button variant="gradient" onClick={saveEdit} disabled={!editMd.trim()}>儲存</Button>
          </div>
        </div>
      </Dialog>

      {generating && <ProgressHint text="AI 正在取材並組織心智圖…" />}
      {regenerating && <ProgressHint text="AI 正在重新取材、重畫這張心智圖…" />}
    </>
  );
}
