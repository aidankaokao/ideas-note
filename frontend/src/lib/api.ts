// 薄 API client（見 reference/frontend/frontend-backend-integration.md §5）
// 一律打同源 /api：dev 由 Vite proxy 轉、prod 由 nginx 反代；BASE 支援子路徑部署。
import { useAuth } from "@/stores/auth";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = useAuth.getState().token;
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (res.status === 401) {
    useAuth.getState().logout();
    throw new Error("請重新登入");
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON 回應 */
    }
    throw new Error(msg);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

/** SSE 串流 POST：每收到一個 `data: {...}` 事件就呼叫 onEvent。 */
async function streamRequest(
  path: string,
  body: unknown,
  onEvent: (ev: Record<string, unknown>) => void
): Promise<void> {
  const token = useAuth.getState().token;
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body ?? {}),
  });
  if (res.status === 401) {
    useAuth.getState().logout();
    throw new Error("請重新登入");
  }
  if (!res.ok || !res.body) {
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON 回應 */
    }
    throw new Error(msg);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith("data: ")) {
        try {
          onEvent(JSON.parse(line.slice(6)));
        } catch {
          /* 略過壞掉的事件 */
        }
      }
    }
  }
}

export const api = {
  get: <T>(p: string) => request<T>(`/api${p}`),
  post: <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "POST", body: JSON.stringify(body ?? {}) }),
  put: <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "PUT", body: JSON.stringify(body ?? {}) }),
  del: <T>(p: string) => request<T>(`/api${p}`, { method: "DELETE" }),
  stream: (p: string, body: unknown, onEvent: (ev: Record<string, unknown>) => void) =>
    streamRequest(`/api${p}`, body, onEvent),
};
