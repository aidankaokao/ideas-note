import { useCallback, useEffect, useState } from "react";
import { Check, KeyRound, Loader2, Palette, Pencil, Plug, Plus, Trash2, Users } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { THEMES, applyTheme, currentTheme } from "@/lib/themes";
import type { ActiveProviders, Provider, User } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useAuth } from "@/stores/auth";
import { usePageHeader } from "@/stores/pageHeader";

const EMPTY_FORM = {
  name: "",
  provider: "openai" as "openai" | "ollama",
  base_url: "https://api.openai.com/v1",
  model: "",
  api_key: "",
  temperature: 0.7,
};

export default function SettingsPage() {
  const me = useAuth((s) => s.user);

  // ── LLM providers ──
  const [providers, setProviders] = useState<Provider[]>([]);
  const [active, setActive] = useState<ActiveProviders>({ chat_provider_id: null, embedding_provider_id: null });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [testing, setTesting] = useState(false);
  const [savingProvider, setSavingProvider] = useState(false);

  // ── 主題 ──
  const [theme, setTheme] = useState(currentTheme());

  // ── 密碼 ──
  const [newPassword, setNewPassword] = useState("");

  // ── 使用者管理（admin）──
  const [userList, setUserList] = useState<User[]>([]);
  const [userDialog, setUserDialog] = useState(false);
  const [userForm, setUserForm] = useState({ username: "", password: "", is_admin: false });

  const loadProviders = useCallback(() => {
    api.get<Provider[]>("/settings/llm-providers").then(setProviders).catch((e) => toast.error((e as Error).message));
    api.get<ActiveProviders>("/settings/llm-active").then(setActive).catch(() => {});
  }, []);

  const loadUsers = useCallback(() => {
    if (!me?.is_admin) return;
    api.get<User[]>("/users").then(setUserList).catch(() => {});
  }, [me?.is_admin]);

  useEffect(() => {
    usePageHeader.getState().set("設定", "LLM、主題與帳號");
    loadProviders();
    loadUsers();
  }, [loadProviders, loadUsers]);

  // ── provider 表單 ──
  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEdit = (p: Provider) => {
    setEditingId(p.id);
    setForm({
      name: p.name,
      provider: p.provider,
      base_url: p.base_url,
      model: p.model,
      api_key: "", // 留空 = 保留舊 key
      temperature: p.temperature,
    });
    setDialogOpen(true);
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const res = await api.post<{ ok: boolean; message: string }>("/settings/llm-providers/test", {
        id: editingId,
        provider: form.provider,
        base_url: form.base_url,
        model: form.model,
        api_key: form.api_key,
      });
      if (res.ok) toast.success(res.message);
      else toast.error(res.message);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTesting(false);
    }
  };

  const saveProvider = async () => {
    if (!form.name.trim() || !form.model.trim() || !form.base_url.trim()) {
      toast.error("名稱、base_url、模型為必填");
      return;
    }
    setSavingProvider(true);
    try {
      if (editingId === null) {
        await api.post("/settings/llm-providers", form);
      } else {
        await api.put(`/settings/llm-providers/${editingId}`, form);
      }
      toast.success("已儲存 provider");
      setDialogOpen(false);
      loadProviders();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingProvider(false);
    }
  };

  const removeProvider = async (id: number) => {
    try {
      await api.del(`/settings/llm-providers/${id}`);
      toast.success("已刪除");
      loadProviders();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const saveActive = async (next: ActiveProviders) => {
    setActive(next);
    try {
      await api.put("/settings/llm-active", next);
      toast.success("已更新選用模型");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  // ── 密碼 ──
  const changePassword = async () => {
    try {
      await api.put("/auth/password", { password: newPassword });
      setNewPassword("");
      toast.success("密碼已更新");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  // ── 使用者管理 ──
  const createUser = async () => {
    try {
      await api.post("/users", userForm);
      toast.success("已新增帳號");
      setUserDialog(false);
      setUserForm({ username: "", password: "", is_admin: false });
      loadUsers();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const resetUserPassword = async (u: User) => {
    const pw = window.prompt(`重設「${u.username}」的密碼：`);
    if (!pw) return;
    try {
      await api.put(`/users/${u.id}`, { password: pw });
      toast.success("密碼已重設");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const removeUser = async (u: User) => {
    if (!window.confirm(`確定刪除「${u.username}」？其筆記與主題會一併刪除。`)) return;
    try {
      await api.del(`/users/${u.id}`);
      toast.success("已刪除帳號");
      loadUsers();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const providerOptions = (
    <>
      <option value="">（未選用）</option>
      {providers.map((p) => (
        <option key={p.id} value={p.id}>{p.name}（{p.model}）</option>
      ))}
    </>
  );

  return (
    <>
      {/* ── LLM Providers ── */}
      <Card className="animate-fade-up">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-5 w-5 text-primary" strokeWidth={1.75} /> LLM Provider
            </CardTitle>
            <Button variant="gradient" size="sm" onClick={openCreate}>
              <Plus strokeWidth={1.75} /> 註冊
            </Button>
          </div>
          <CardDescription>可註冊多個（OpenAI / Ollama / vLLM 相容），再選用給對話與 embedding。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {providers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              尚未註冊任何 provider——AI 功能（延伸、問答、心智圖）需要先在這裡註冊並選用。
            </p>
          ) : (
            <div className="space-y-2">
              {providers.map((p) => (
                <div key={p.id} className="glass-soft flex flex-wrap items-center gap-2 rounded-2xl px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{p.name}</span>
                      <Badge variant={p.provider === "openai" ? "indigo" : "teal"}>{p.provider}</Badge>
                    </div>
                    <p className="truncate text-xs text-muted-foreground">
                      {p.model} · {p.base_url}{p.api_key ? ` · ${p.api_key}` : ""}
                    </p>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(p)}>
                    <Pencil className="!size-3.5" strokeWidth={1.75} />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => removeProvider(p.id)}>
                    <Trash2 className="!size-3.5" strokeWidth={1.75} />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>對話模型（延伸 / 問答 / 心智圖）</Label>
              <Select
                value={active.chat_provider_id ?? ""}
                onChange={(e) =>
                  saveActive({ ...active, chat_provider_id: e.target.value ? Number(e.target.value) : null })
                }
              >
                {providerOptions}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Embedding 模型（相關檢索）</Label>
              <Select
                value={active.embedding_provider_id ?? ""}
                onChange={(e) =>
                  saveActive({ ...active, embedding_provider_id: e.target.value ? Number(e.target.value) : null })
                }
              >
                {providerOptions}
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── 主題盤 ── */}
      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-primary" strokeWidth={1.75} /> 主題盤
          </CardTitle>
          <CardDescription>玻璃結構不變，只換配色。</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-3 sm:grid-cols-8">
            {THEMES.map((t) => (
              <button
                key={t.id}
                title={t.name}
                onClick={() => {
                  applyTheme(t.id);
                  setTheme(t.id);
                }}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-2xl p-2 transition-colors hover:bg-white/50",
                  theme === t.id && "bg-white shadow-sm"
                )}
              >
                <span
                  className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
                  style={{ backgroundImage: `linear-gradient(to bottom right, ${t.from}, ${t.to})` }}
                >
                  {theme === t.id && <Check className="h-4 w-4" strokeWidth={2.5} />}
                </span>
                <span className="text-[10px] text-muted-foreground">{t.name}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── 修改密碼 ── */}
      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5 text-primary" strokeWidth={1.75} /> 修改密碼
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-48 flex-1 space-y-1.5">
              <Label htmlFor="new-password">新密碼</Label>
              <Input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <Button onClick={changePassword} disabled={newPassword.length < 4}>更新密碼</Button>
          </div>
        </CardContent>
      </Card>

      {/* ── 使用者管理（管理員）── */}
      {me?.is_admin && (
        <Card className="animate-fade-up">
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" strokeWidth={1.75} /> 使用者管理
              </CardTitle>
              <Button variant="gradient" size="sm" onClick={() => setUserDialog(true)}>
                <Plus strokeWidth={1.75} /> 新增帳號
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {userList.map((u) => (
              <div key={u.id} className="glass-soft flex items-center gap-2 rounded-2xl px-4 py-2.5">
                <span className="min-w-0 flex-1 truncate text-sm font-medium">{u.username}</span>
                {u.is_admin && <Badge>管理員</Badge>}
                <Button variant="ghost" size="icon" className="h-8 w-8" title="重設密碼" onClick={() => resetUserPassword(u)}>
                  <KeyRound className="!size-3.5" strokeWidth={1.75} />
                </Button>
                {u.id !== me.id && (
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" title="刪除" onClick={() => removeUser(u)}>
                    <Trash2 className="!size-3.5" strokeWidth={1.75} />
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── provider 表單 Dialog ── */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editingId === null ? "註冊 LLM Provider" : "編輯 LLM Provider"}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>顯示名稱</Label>
            <Input
              placeholder="例：OpenAI 主力"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>類型</Label>
              <Select
                value={form.provider}
                onChange={(e) => {
                  const provider = e.target.value as "openai" | "ollama";
                  setForm({
                    ...form,
                    provider,
                    base_url:
                      provider === "ollama" ? "http://localhost:11434" : "https://api.openai.com/v1",
                  });
                }}
              >
                <option value="openai">openai（OpenAI / vLLM 相容）</option>
                <option value="ollama">ollama（本地）</option>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>temperature</Label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>base_url</Label>
            <Input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>模型</Label>
            <Input
              placeholder="例：gpt-4o-mini / text-embedding-3-small"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
          </div>
          {form.provider === "openai" && (
            <div className="space-y-1.5">
              <Label>API Key{editingId !== null && "（留空＝保留原本的）"}</Label>
              <Input
                type="password"
                autoComplete="off"
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              />
            </div>
          )}
          <div className="flex justify-between gap-2 pt-1">
            <Button variant="outline" onClick={testConnection} disabled={testing}>
              {testing ? <Loader2 className="animate-spin" /> : <Plug strokeWidth={1.75} />}
              測試連線
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setDialogOpen(false)}>取消</Button>
              <Button variant="gradient" onClick={saveProvider} disabled={savingProvider}>
                {savingProvider && <Loader2 className="animate-spin" />}
                儲存
              </Button>
            </div>
          </div>
        </div>
      </Dialog>

      {/* ── 新增帳號 Dialog ── */}
      <Dialog open={userDialog} onClose={() => setUserDialog(false)} title="新增帳號">
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>帳號</Label>
            <Input value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>密碼</Label>
            <Input
              type="password"
              autoComplete="new-password"
              value={userForm.password}
              onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4 accent-[var(--brand-to)]"
              checked={userForm.is_admin}
              onChange={(e) => setUserForm({ ...userForm, is_admin: e.target.checked })}
            />
            設為管理員
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setUserDialog(false)}>取消</Button>
            <Button variant="gradient" onClick={createUser} disabled={!userForm.username || !userForm.password}>
              新增
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
