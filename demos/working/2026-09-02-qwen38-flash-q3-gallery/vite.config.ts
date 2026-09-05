import { defineConfig } from "vite";

/**
 * The gallery is a static, local-only bundle: relative asset URLs mean the
 * built `dist/` folder can be served from any path or port, and every image is
 * copied from `public/images/` rather than fetched from a remote host.
 */
export default defineConfig({
  base: "./",
  publicDir: "public",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    target: "es2022",
    assetsInlineLimit: 0
  },
  server: { host: "127.0.0.1", port: 5173 },
  preview: { host: "127.0.0.1", port: 4173 }
});
