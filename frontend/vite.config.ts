// Vite 設定（照 reference/frontend 起手檔）— React + TS，@ 別名，dev proxy 到後端，子路徑 build 支援。
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  // 路由部署：build 時給 VITE_BASE_PATH=/<APP_ROUTE>/；本機 dev 仍是 /。
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
