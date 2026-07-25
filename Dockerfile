# Cloud Run 單一容器：先 build 前端靜態檔，再塞進 FastAPI 一起跑。
# （部署細節見 docs/DEPLOY-CLOUD-RUN.md）

# ── Stage 1：build 前端 ──
FROM node:20-slim AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ ./
ENV VITE_BASE_PATH=/
RUN npm run build

# ── Stage 2：後端＋靜態檔 ──
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend /app/dist ./static
ENV APP_ENV=prod
# Cloud Run 會注入 PORT=8080，api.py 會讀取
CMD ["python", "api.py"]
