# 前後端接線慣例（Dev Proxy / Nginx / API Client · 可攜式）

> 把「前端怎麼跟後端串」講清楚，讓三種前端風格都能無痛接上 `backend/`（FastAPI，port 8000，路徑前綴 `/api`）。
> **核心心法：前端一律呼叫同源相對路徑 `/api/...`**，開發期由 Vite dev proxy 轉給後端，正式期由前端容器的 nginx 反代給後端。前端程式碼**不需要知道後端主機 / port**，dev 與 prod 都不用改。

---

## 0. 一句話總結

前端只打 `fetch("/api/...")`（同源相對路徑）→
- **開發**：Vite dev server 的 `proxy` 把 `/api` 轉到 `http://localhost:8000`。
- **正式**：前端 nginx 的 `location /api/` 把它 `proxy_pass` 到 compose 內的 `backend:8000`。

因此 **prod 不需要 CORS、後端 port 不必對外**（呼應 `../deploy/deploy-guide.md`：後端 `ports` 平時註解掉）。

---

## 1. 後端側前提（來自 backend-conventions.md）

- 後端所有路由前綴 **`/api`**（如 `/api/health`、`/api/chat`）。
- 容器內固定 `host 0.0.0.0` / `port 8000`。
- 開發期 `api.py` 的 CORS 可先 `allow_origins=["*"]`；**正式期因為走 nginx 同源反代，其實不需要 CORS**（見 §4）。

---

## 2. 開發期：Vite dev proxy

`vite.config.ts`（起手檔已附）把 `/api` 代理到本機後端：

```ts
// vite.config.ts（節錄）
export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",   // 本機直接跑的 python api.py
        changeOrigin: true,
      },
    },
  },
});
```

開發流程：
```bash
# 終端 1：後端
cd backend && python api.py          # http://localhost:8000

# 終端 2：前端
cd frontend && npm run dev           # http://localhost:5173，/api 自動轉到 8000
```

前端程式打 `/api/...` 即可，Vite 幫你轉，**不會有 CORS 問題**。

---

## 3. 正式期：前端 nginx 反代（`frontend/nginx.conf`）

前端 build 成靜態檔由 nginx 伺服（見 `../deploy/Dockerfile.frontend`），同一個 nginx 再把 `/api` 反代到後端容器。**這份 `nginx.conf` 就是先前 Dockerfile 一直 `COPY` 需要的檔**（起手檔已附）。

> **兩個版本，依部署方式選：**
> - **根路徑版 `nginx.conf`**（掛 `/`）—— 純內網、直接 `ip:port/` 存取、未來不綁 DNS route。就是下面這份。
> - **路由版 `nginx.conf.template`**（掛 `/<APP_ROUTE>/`，**推薦**）—— 內網 `ip:port/<route>/` 與外網 `DNS/<route>/` 共用同一 build。見 **§6**。

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript application/xml+rss image/svg+xml;

    # 前端 SPA：找不到實體檔就回 index.html（前端路由用）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # /api 反代到後端容器：compose 的 service 名稱是 backend，內埠 8000
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE / 串流（LLM 逐字輸出）必要：關 buffering、拉長 timeout
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```

要點：
- `proxy_pass http://backend:8000;` 的 `backend` 是 **docker-compose service 名稱**（見 deploy guide），兩者要一致。
- 前端與後端在同一 `custom-network` 內，nginx 用內網直接找到 `backend`，**後端 port 不必對外**。
- **SSE / 串流**：`proxy_buffering off` + 長 `proxy_read_timeout`，否則 LLM 逐字輸出會被卡住。
- SPA fallback（`try_files ... /index.html`）讓前端路由（React Router）重新整理不 404。

---

## 4. 為什麼 prod 不用 CORS

因為使用者瀏覽器只跟**前端 nginx 同源**（同一個 host:port）互動，`/api` 是同源路徑、由 nginx 內部轉發，瀏覽器不會觸發跨來源檢查。所以：
- **開發**：靠 Vite proxy，同源，無 CORS。
- **正式**：靠 nginx 反代，同源，無 CORS。
- 只有在你**刻意讓前端直連後端對外 port**（跳過 nginx）時才需要 CORS —— 一般不這樣做。

---

## 5. 前端 API client（fetch 包裝 + 錯誤處理）

前端統一用一個薄 client 打 `/api`，集中處理錯誤與 JSON，**別散落 `fetch`**。回應失敗就丟出、由呼叫端接住並用 toast 呈現（toast 樣式見各風格文件）。

```ts
// src/lib/api.ts
const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");  // 支援子路徑部署（見 §6）

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    // 後端慣例：錯誤回 { detail: "..." }（FastAPI 預設）
    let msg = `HTTP ${res.status}`;
    try { msg = (await res.json()).detail ?? msg; } catch { /* 非 JSON */ }
    throw new Error(msg);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  get:  <T>(p: string) => request<T>(`/api${p}`),
  post: <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "POST", body: JSON.stringify(body) }),
  put:  <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "PUT", body: JSON.stringify(body) }),
  del:  <T>(p: string) => request<T>(`/api${p}`, { method: "DELETE" }),
};
```

用法（呼叫端接錯誤 → toast）：
```ts
try {
  const items = await api.get<Item[]>("/items");
} catch (e) {
  toast.error((e as Error).message);   // sonner / shadcn toast，見風格文件
}
```

**串流（LLM 逐字）**：用 `fetch` 讀 `res.body` 的 `ReadableStream`（SSE / chunked），逐段更新畫面。前端「多秒操作進度」呈現慣例見各風格文件。

---

## 6. 路由部署機制（`APP_ROUTE`：內外網共用 `/<route>/`）

**推薦作法**：把整個前端掛在一個 route 名稱（`APP_ROUTE`）底下，讓內網與外網共用**同一份 build**，未來綁 DNS 不用改程式。

| 環境 | 存取網址 |
|---|---|
| **內網**（直接 ip:port）| `http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/` |
| **外網**（團隊 nginx 綁 DNS）| `https://<DNS>/<APP_ROUTE>/` → 反代到上面 ip:port，**路徑原樣轉發、不 rewrite** |

一個 `APP_ROUTE` 貫穿三處，務必一致（都來自根目錄 `.env` 的 `APP_ROUTE`）：

1. **前端 build**：`VITE_BASE_PATH=/<APP_ROUTE>/`（`build.sh` 帶入）→ Vite 把資源路徑與 `import.meta.env.BASE_URL` 都設成 `/<APP_ROUTE>/`。
2. **前端 nginx**：用 `nginx.conf.template`（容器啟動 envsubst 讀 `APP_ROUTE`），把 SPA 掛在 `location /<APP_ROUTE>/`、API 掛在 `location /<APP_ROUTE>/api/`（`proxy_pass` 帶 URI 會把前綴改回後端的 `/api/`）。
3. **前端 API 呼叫**：§5 的 `api.ts` 用 `import.meta.env.BASE_URL` 組路徑（`BASE = /<APP_ROUTE>`），所以自動打 `/<APP_ROUTE>/api/...`，同源、免 CORS。**程式不需寫死 route**。

要點與注意：
- route 在 **build 時**烤進前端，**改 route 要重新 build 前端 image**（`build.sh` 從 `.env` 讀 `APP_ROUTE`）。
- 後端**不需要知道 route**：nginx 會把 `/<APP_ROUTE>/api/` 反代成後端的 `/api/`，後端維持只認 `/api`。
- 團隊 nginx 綁 DNS 時，`https://<DNS>/<APP_ROUTE>/` 直接 `proxy_pass` 到 `http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/` 即可（同 path，不需改寫）。
- **開發期**（Vite dev，§2）仍是根路徑 `http://localhost:5173/`，`BASE_URL=/`，API 打 `/api` 由 dev proxy 轉——route 只影響正式 build，本機開發不受影響。
- 純內網、確定不綁 DNS 也不要 route → 用根路徑版 `nginx.conf`（§3）+ `VITE_BASE_PATH=/`（`APP_ROUTE` 留空）。

> 完整的 compose / Dockerfile / build.sh / .env 怎麼串這個 `APP_ROUTE`，見 `../deploy/deploy-guide.md`「路由機制」段。

---

## 7. 頁面標題 store（集中式 Header 標題）

各風格文件的 Header 都採「集中式標題」：各頁透過一個小 store 設定「標題 + 副標」，Header 讀取顯示。用 zustand 一個極小 store 即可：

```ts
// src/stores/pageHeader.ts
import { create } from "zustand";

type State = { title: string; subtitle?: string; set: (t: string, s?: string) => void };
export const usePageHeader = create<State>((set) => ({
  title: "",
  set: (title, subtitle) => set({ title, subtitle }),
}));
```

頁面 `useEffect(() => usePageHeader.getState().set("標題", "副標"), [])`；Header 讀 `usePageHeader()`。

---

## 8. 慣例小結

- 前端一律打**同源相對路徑 `/api/...`**；dev 靠 Vite proxy、prod 靠 nginx 反代，程式不分環境。
- `frontend/nginx.conf`：SPA fallback + `/api` 反代到 `backend:8000` + 串流關 buffering（**填掉 Dockerfile 一直要 COPY 的那個檔**）。
- **prod 同源 → 不用 CORS**；後端 port 不必對外（呼應 deploy guide）。
- API 走 `src/lib/api.ts` 薄 client，錯誤丟出由呼叫端 toast。
- **路由部署**：前端掛 `/<APP_ROUTE>/`（`nginx.conf.template`），內網 `ip:port/<route>/`、外網 `DNS/<route>/` 共用同一 build；`APP_ROUTE` 貫穿 build（`VITE_BASE_PATH`）＋ nginx ＋ API 路徑（`BASE_URL`），改 route 要重 build。
- Header 標題用集中式 store。
