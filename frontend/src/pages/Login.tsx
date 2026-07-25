import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { GlassBackground } from "@/components/GlassBackground";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { useAuth } from "@/stores/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const login = useAuth((s) => s.login);
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username || !password || busy) return;
    setBusy(true);
    try {
      const res = await api.post<{ token: string; user: User }>("/auth/login", {
        username,
        password,
      });
      login(res.token, res.user);
      navigate("/", { replace: true });
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <GlassBackground />
      <div className="flex min-h-dvh items-center justify-center p-4">
        <Card className="w-full max-w-sm p-6 animate-fade-up">
          <div className="mb-6 flex flex-col items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white">
              <Sparkles className="h-7 w-7" strokeWidth={1.75} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="text-gradient">靈感筆記</span>
            </h1>
            <p className="text-sm text-muted-foreground">記下靈感，讓 AI 幫你延伸與整理</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">帳號</Label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">密碼</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button type="submit" variant="gradient" className="w-full" disabled={busy}>
              {busy && <Loader2 className="animate-spin" />}
              登入
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            初次使用：預設帳號 admin / admin，登入後請到「設定」修改密碼
          </p>
        </Card>
      </div>
    </>
  );
}
