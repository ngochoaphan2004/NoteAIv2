import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "127.0.0.1",
    port: 5173,
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          "vendor-react": ["react", "react-dom"],
          // KaTeX (math rendering) — rất nặng, tách riêng
          "vendor-katex": ["katex", "rehype-katex", "remark-math"],
          // Markdown rendering
          "vendor-markdown": ["react-markdown", "remark-gfm", "rehype-raw"],
          // Charts
          "vendor-recharts": ["recharts"],
          // React Query
          "vendor-query": ["@tanstack/react-query"],
          // Icons
          "vendor-icons": ["lucide-react"],
        },
      },
    },
  },
});
