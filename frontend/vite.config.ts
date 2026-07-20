import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev server proxies API calls to a locally-running uvicorn instance.
// The production build is served by FastAPI itself (same origin).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/ui/api": "http://127.0.0.1:8000",
    },
  },
});
