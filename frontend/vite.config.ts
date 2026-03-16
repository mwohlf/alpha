import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// defineConfig provides fantastic TypeScript autocompletion for your Vite config
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "build",
  },
  server: {
    port: 3000, // <-- Add this to set your custom port
    strictPort: true, // <-- (Optional) Set to true to exit if port 3000 is already in use
    proxy: {
      // Assuming your frontend calls '/api/something' to reach the Python backend
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // Optional: If your Python API doesn't actually have '/api' in the URL route,
        // you can rewrite the path before it hits the backend:
        // rewrite: (path) => path.replace(/^\/api/, '')
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/setupTests.ts"],
    globals: true,
  },
});
