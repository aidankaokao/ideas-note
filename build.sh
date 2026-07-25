#!/usr/bin/env bash
# build 起手檔。複製到專案【根目錄】。compose 不 build，所以先用這支把 image build 好、打 tag。
# tag 要和 docker-compose.yaml 的 image: 完全一致。加 --no-cache 強制重 build。
# 前端會依 APP_ROUTE 把 route 烤進 build（VITE_BASE_PATH=/<APP_ROUTE>/），與 nginx template 對齊。
# 需個別 build 時自己註解掉其他行。

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
