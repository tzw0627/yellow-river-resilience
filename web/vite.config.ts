import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import cesium from "vite-plugin-cesium";

// 开发期把 /data 与 /api 代理到 FastAPI（默认 8000 端口），
// 这样前端可继续用相对路径加载 overlay/查询网格，并调用后端智能体/报告接口。
export default defineConfig({
  plugins: [vue(), cesium()],
  server: {
    port: 5173,
    proxy: {
      "/data": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
