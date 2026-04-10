import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const rewriteRootToApp = () => ({
  name: "rewrite-root-to-app",
  configureServer(server: any) {
    server.middlewares.use((req: any, res: any, next: any) => {
      if (req.url === "/" || req.url === "/index.html" || req.url === "/app") {
        res.writeHead(302, { Location: "/app/" });
        res.end();
        return;
      }
      next();
    });
  },
});

const startupMsg = () => ({
  name: "custom-startup-message",
  configureServer(server: any) {
    // Save the original printUrls method
    const originalPrintUrls = server.printUrls;
    // Override printUrls
    server.printUrls = () => {
      // Call the original first to print the Local/Network URLs
      originalPrintUrls();
      console.log(" ➜  Welcome to the Dev Server!");
      console.log(" Local also available at: http://localhost:3000/");
    };
  },
});

// defineConfig provides fantastic TypeScript autocompletion for your Vite config
export default defineConfig({
  root: __dirname, // This tells Vite the project starts inside the 'frontend' folder
  base: "/app/", // prefix for routes, used in the fastAPI setup
  cacheDir: "../node_modules/.vite/frontend",
  plugins: [react(), rewriteRootToApp(), startupMsg()],
  build: {
    outDir: "build",
    emptyOutDir: true,
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
  server: {
    port: 3000,
    strictPort: true, // exit if port 3000 is already in use
    proxy: {
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
