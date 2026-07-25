// Vite 設定（起手檔）— React + TS，@ 別名，dev proxy 到後端，子路徑 build 支援。
// 說明見 frontend-backend-integration.md §2、§6。
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  // 路由部署：build 時給 VITE_BASE_PATH=/<APP_ROUTE>/（build.sh 從 .env 的 APP_ROUTE 帶入）；
  // 預設根路徑 /。本機 dev 不受影響，仍是 /。見 frontend-backend-integration.md §6。
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    proxy: {
      // 前端一律打同源 /api，開發期由這裡轉給本機後端（python api.py, port 8000）
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
