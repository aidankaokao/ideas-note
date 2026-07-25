# 部署慣例（Docker Compose · 可攜式）

> 這份文件把我的**容器打包與部署慣例**抽離成一份自足規範，
> 目的是：**新的 Claude Code session 只看這一份，就能照我習慣的方式產出 `docker-compose.yaml` / `Dockerfile` / `build.sh` / `.env`。**
> 下面的檔案內容都是**模板**，直接複製到專案根目錄改用。

---

## 0. 一句話總結（我的部署習慣，務必遵守）

- **自己 build image，compose 只寫 `image` 不寫 `build`**：由 `build.sh` 先把 image build 好並打 tag，`docker-compose.yaml` 直接引用 `image:` 名稱。
- **用舊命令 `docker-compose up -d`**（連字號版，不是 `docker compose`）。
- **每個 service 一定要有 `logging` 與 `labels`**。
- **後端 port 映射要寫出來但註解掉**：開發期打開查看，上線註解回去不對外。
- **所有容器對外 port 都走 `.env` 設定**，才能依實際情況改，不寫死在 compose。
- **前端掛在一個 route 底下**（`APP_ROUTE`），讓內網 `ip:port/<route>/` 與外網 `DNS/<route>/` 共用同一份 build（見下方路由機制）。

---

## 路由機制：內外網共用 `/<APP_ROUTE>/`（先看這個）

專案一律把前端掛在一個 **route 名稱**（`APP_ROUTE`，放根目錄 `.env`）底下，讓內網與外網**共用同一份 build**，未來綁 DNS 不用改程式：

| 環境 | 存取網址 |
|---|---|
| **內網**（直接 ip:port）| `http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/` |
| **外網**（團隊 nginx 綁 DNS）| `https://<DNS>/<APP_ROUTE>/` → 反代到上面那個 ip:port，**路徑原樣轉發、不 rewrite** |

一個 `APP_ROUTE` 貫穿三處，**務必一致**：
1. **前端 build**：`VITE_BASE_PATH=/<APP_ROUTE>/`（由 `build.sh` 帶入，見 §6），資源路徑與 `BASE_URL` 都掛 route。
2. **前端 nginx**：用 `nginx.conf.template`（容器啟動 envsubst 讀 `APP_ROUTE`），location 掛 `/<APP_ROUTE>/` 與 `/<APP_ROUTE>/api/`。
3. **前端 API 呼叫**：走 `import.meta.env.BASE_URL` 組路徑，自動打 `/<APP_ROUTE>/api/...`（見 `../frontend/frontend-backend-integration.md` §5、§6）。

- 因為 route 在 build 時就烤進前端，**改 route 要重新 build 前端 image**。
- 團隊 nginx 綁 DNS 時，把 `https://<DNS>/<APP_ROUTE>/` 直接 `proxy_pass` 到 `http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/` 即可（同 path，不需 rewrite）。
- **後端不需要知道 route**：前端 nginx 會把 `/<APP_ROUTE>/api/` 反代成後端的 `/api/`，後端維持只認 `/api`。
- 純內網、確定不綁 DNS 也不要 route → 改用根路徑版 `../frontend/nginx.conf` + `VITE_BASE_PATH=/`（`APP_ROUTE` 留空）。

---

## 1. 檔案清單（放專案根目錄）

```
專案根/
├── docker-compose.yaml        # 只寫 image，不寫 build；含 logging + labels
├── build.sh                   # 自己 build image 的腳本（打 tag）
├── .env                       # 對外 port / labels 變數（不進版控）
├── .env.example               # 範例（進版控）
├── Dockerfile.backend         # 後端 image（python:3.11-slim，CMD python api.py）
├── Dockerfile.frontend        # 前端 image（node build → nginx）
├── backend/                   # 見 ../backend/backend-conventions.md
│   └── .env                   # 後端「應用層」env（DB / LLM 等，與部署層 .env 分開）
└── frontend/
    └── nginx.conf
```

> **兩種 `.env` 要分清楚**：根目錄 `.env` 是**部署層**（對外 port、labels，compose 讀）；`backend/.env` 是**應用層**（DB_URL、LLM 設定，backend 程式讀，見 `../backend/backend-conventions.md` §5）。

---

## 2. `docker-compose.yaml`（模板）

要點：`image:` 不寫 `build:`；每個 service 有 `logging` + `labels`；**後端 ports 寫出來但註解**；對外 port 走 `.env`。

```yaml
version: "3.8"

services:
  backend:
    image: ${IMAGE_PREFIX}-backend:${IMAGE_TAG}   # 命名走 .env（見 build.sh），不寫 build:
    container_name: ${IMAGE_PREFIX}-backend
    env_file: backend/.env                   # 後端應用層 env（DB / LLM）
    volumes:
      - ./backend/data:/app/backend/data     # SQLite 檔 / 產出（見 database.md）
    # ── 後端對外 port：開發期打開查看，上線時整段註解掉不對外 ──
    # ports:
    #   - "${BACKEND_PORT}:8000"             # 容器內固定 8000（api.py 寫死），對外走 .env
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    labels:
      - "developer=${DEVELOPER_NAME}"
      - "project.path=${PROJECT_PATH}"
    restart: unless-stopped
    networks:
      - custom-network

  frontend:
    image: ${IMAGE_PREFIX}-frontend:${IMAGE_TAG}  # 命名走 .env
    container_name: ${IMAGE_PREFIX}-frontend
    environment:
      - APP_ROUTE=${APP_ROUTE}               # nginx.conf.template envsubst 用（把前端掛在 /<route>/）
    ports:
      - "${FRONTEND_PORT}:80"                # 對外 FRONTEND_PORT → 容器 80；實際入口 /<APP_ROUTE>/
    depends_on:
      - backend
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    labels:
      - "developer=${DEVELOPER_NAME}"
      - "project.path=${PROJECT_PATH}"
    restart: unless-stopped
    networks:
      - custom-network

networks:
  custom-network:
    external: true                           # 用外部既有網路
    name: ${NETWORK_NAME}
```

說明：
- **image / container / 網路命名全走 `.env`**（`IMAGE_PREFIX` / `IMAGE_TAG` / `NETWORK_NAME`）—— 換新專案只改 `.env`，compose 與 `build.sh` 同時生效，不必逐檔改名。
- **`image:` 而非 `build:`** —— image 由 `build.sh` 先 build 好。
- **後端 `ports` 註解掉**：開發要看後端就把那兩行取消註解（`BACKEND_PORT:8000`），上線再註解回去，後端只透過 `custom-network` 給前端 / nginx 內部存取。
- **容器內埠固定 8000**（`api.py` 寫死，見 `../backend/backend-conventions.md` §3），**對外埠由 `.env` 的 `BACKEND_PORT` / `FRONTEND_PORT` 決定**。
- `logging` 用 `json-file` + 滾動（`max-size` / `max-file`），每個 service 都要有。
- `labels` 至少帶 `developer` / `project.path`（走 `.env`），方便盤點容器歸屬。
- `networks` 用 `external: true` 既有網路；沒有的話先建：`docker network create "$NETWORK_NAME"`（名稱＝`.env` 的 `NETWORK_NAME`）。

---

## 3. `.env` / `.env.example`（部署層，對外 port + labels）

```dotenv
# ── image / 網路命名（只改這裡；compose 與 build.sh 都吃同一組）──
IMAGE_PREFIX=myapp
IMAGE_TAG=0.1
NETWORK_NAME=myapp-network

# ── 路由名稱（內外網共用；見上方路由機制）──
# 前端掛在 /<APP_ROUTE>/：內網 http://<ip>:<FRONTEND_PORT>/<APP_ROUTE>/、外網 https://<DNS>/<APP_ROUTE>/
# 不含前後斜線。改動後前端 image 需重新 build（VITE_BASE_PATH 由它帶入）。
APP_ROUTE=myapp

# ── 對外 port（依實際情況改，不寫死在 compose）──
FRONTEND_PORT=8080
BACKEND_PORT=8000          # 僅開發期打開後端 ports 時用到

# ── labels（容器歸屬盤點）──
DEVELOPER_NAME=aidan
PROJECT_PATH=/home/aidan/projects/myapp
```

> 這份 `.env` 給 `docker-compose` 讀（變數展開到 compose）。**不進版控**，另留 `.env.example` 當範例。

---

## 4. `Dockerfile.backend`（模板）

Python 3.11、容器內埠 8000、`CMD ["python", "api.py"]`（呼應 `api.py` 內建 `uvicorn.run`）。

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ /app/backend/

RUN mkdir -p /app/backend/data      # SQLite 檔 / 產出（掛 volume）

WORKDIR /app/backend

EXPOSE 8000                         # 容器內埠，對外由 compose .env 映射

CMD ["python", "api.py"]            # api.py 底部有 uvicorn.run(host=0.0.0.0, port=8000)
```

> 若後端需要系統套件（如中文字體、繪圖 / PDF 依賴），在 `pip install` 前加一段 `apt-get install`（參考本專案舊 Dockerfile 的字體 / cairo / pango 安裝段）。

> **`frontend/nginx.conf` 是必要檔**（§5 的 `Dockerfile.frontend` 會 `COPY` 它）：負責 SPA fallback + 把 `/api` 反代到 `backend:8000`。現成範本見 `../frontend/nginx.conf`，設計理由見 `../frontend/frontend-backend-integration.md`。**沒有這份檔前端 build 會失敗。**

---

## 5. `Dockerfile.frontend`（模板）

多階段：node build → nginx 靜態伺服；支援子路徑部署（`VITE_BASE_PATH`）。

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY frontend/ .

# 子路徑部署支援：build 時可指定 base path（預設 /）。
# 例：docker build --build-arg VITE_BASE_PATH=/myapp/ ...
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# 路由版（推薦）：用 nginx template，容器啟動時 envsubst 讀 APP_ROUTE 代換（見 frontend/nginx.conf.template）
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
# 純根路徑、不要 route 時，改成下一行（並讓 APP_ROUTE 留空 / VITE_BASE_PATH=/）：
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

> nginx 官方 image 會自動把 `/etc/nginx/templates/*.template` 用 `envsubst` 代換環境變數後輸出到 `/etc/nginx/conf.d/`。只會代換有定義的 env 變數（如 `APP_ROUTE`），`$uri` / `$host` 等 nginx 內建變數不受影響。`APP_ROUTE` 由 compose 的 `environment` 帶入（§2）。

---

## 6. `build.sh`（模板）— 自己 build image、打 tag

`docker-compose.yaml` 不 build，所以先用這支把 image build 好。tag 要和 compose 的 `image:` 完全一致。

```bash
#!/usr/bin/env bash
# 一鍵 build 所有 image。需個別 build 時自己註解掉其他行。加 --no-cache 強制重 build。
# 前端會依 APP_ROUTE 把 route 烤進 build（VITE_BASE_PATH=/<APP_ROUTE>/），與 nginx template 對齊。

cd "$(dirname "$0")"

# 從同目錄 .env 讀命名與 route（也可直接寫死）
set -a; [ -f .env ] && . ./.env; set +a
IMAGE_PREFIX="${IMAGE_PREFIX:-myapp}"
IMAGE_TAG="${IMAGE_TAG:-0.1}"
APP_ROUTE="${APP_ROUTE:-myapp}"

docker build --no-cache -f Dockerfile.backend  -t "${IMAGE_PREFIX}-backend:${IMAGE_TAG}"  .
docker build --no-cache \
  --build-arg VITE_BASE_PATH="/${APP_ROUTE}/" \
  -f Dockerfile.frontend -t "${IMAGE_PREFIX}-frontend:${IMAGE_TAG}" .
```

- **命名一致性**：image tag 由 `.env` 的 `IMAGE_PREFIX` / `IMAGE_TAG` 決定，`build.sh` 與 `docker-compose.yaml` 讀同一組，**改名只動 `.env`**、不必逐檔改。
- **route 一致性**：`build.sh` 的 `VITE_BASE_PATH=/<APP_ROUTE>/` 與 compose 給 nginx 的 `APP_ROUTE` 都來自同一個 `.env`，改 route 記得重跑 `build.sh`。
- build context 是專案根（`.`），所以 Dockerfile 內用 `COPY backend/...` / `COPY frontend/...`。

---

## 7. 部署流程（照這個順序）

```bash
# 0. 首次：準備 .env、建外部網路
cp .env.example .env                      # 改 IMAGE_PREFIX / APP_ROUTE / FRONTEND_PORT / DEVELOPER_NAME ...
set -a; . ./.env; set +a                  # 載入變數（下一行的 NETWORK_NAME 要用）
docker network create "$NETWORK_NAME"     # 已存在就跳過

# 1. 準備後端應用層 .env
cp backend/.env.example backend/.env      # 改 DB / LLM 設定（見 backend-conventions.md）

# 2. 自己 build image
bash build.sh                             # 或 ./build.sh

# 3. 起服務（用舊命令 docker-compose）
docker-compose up -d

# 前端入口（內網）：http://<本機/伺服器 ip>:<FRONTEND_PORT>/<APP_ROUTE>/
#   例：http://192.168.1.20:8080/myapp/
# 之後綁 DNS：https://<DNS>/<APP_ROUTE>/（團隊 nginx 反代到上面 ip:port）

# 檢視
docker-compose ps
docker-compose logs -f backend            # 開發期看後端 log

# 更新（改版）：重 build 再 up
bash build.sh && docker-compose up -d

# 收掉
docker-compose down
```

---

## 8. 開發 ↔ 上線切換

| 項目 | 開發期 | 上線 |
|---|---|---|
| 後端對外 port | `docker-compose.yaml` 的 `backend.ports` **取消註解**，用 `BACKEND_PORT` 看後端 | **註解回去**，後端只走內網 `custom-network` |
| CORS | `allow_origins=["*"]` | 收斂成前端實際來源（`api.py`）|
| uvicorn reload | 可用 `reload=True` 本機跑 | 容器內**不開** reload（`CMD python api.py`）|
| 對外 port | `.env` 設好對外埠 | 依伺服器實際情況改 `.env` |

---

## 9. 慣例小結

- **compose 只 `image` 不 `build`**；image 用 `build.sh` 自己 build。**image / 網路命名全走 `.env`**（`IMAGE_PREFIX` / `IMAGE_TAG` / `NETWORK_NAME`），換專案只改 `.env`。
- **`docker-compose up -d`**（舊命令）。
- 每個 service 都要 **`logging`（json-file + 滾動）** 與 **`labels`（developer / project.path）**。
- **後端 `ports` 寫出來但註解**：開發打開、上線註解。
- **對外 port 全走根目錄 `.env`**（`FRONTEND_PORT` / `BACKEND_PORT`）；容器內埠固定（後端 8000 / 前端 80）。
- **route 機制**：前端掛 `/<APP_ROUTE>/`，內網 `ip:port/<route>/`、外網 `DNS/<route>/` 共用同一 build；`APP_ROUTE` 貫穿 build（`VITE_BASE_PATH`）＋ nginx template ＋ 前端 API 路徑，改 route 要重 build。
- 部署層 `.env`（compose）與應用層 `backend/.env`（程式）分開。
