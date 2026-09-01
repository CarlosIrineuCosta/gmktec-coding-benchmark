import { readFileSync } from "node:fs";
import path from "node:path";
import { defineConfig, type Plugin } from "vite";

/**
 * The image corpus and its `images.json` manifest ship as public assets.
 * Rather than fetching the manifest at runtime (an extra request that can
 * fail, and an extra paint of an empty gallery) we surface it to the app as a
 * build-time virtual module. One source of truth: `public/images.json`.
 */
const MANIFEST_VIRTUAL_ID = "virtual:gallery-manifest";
const MANIFEST_RESOLVED_ID = `\0${MANIFEST_VIRTUAL_ID}`;

function galleryManifestPlugin(): Plugin {
  let manifestPath = "";
  return {
    name: "gallery-manifest",
    configResolved(config) {
      manifestPath = path.resolve(config.root, "public/images.json");
    },
    resolveId(id) {
      return id === MANIFEST_VIRTUAL_ID ? MANIFEST_RESOLVED_ID : null;
    },
    load(id) {
      if (id !== MANIFEST_RESOLVED_ID) return null;
      const items: unknown = JSON.parse(readFileSync(manifestPath, "utf8"));
      if (!Array.isArray(items)) {
        throw new Error(`${manifestPath} must contain a JSON array`);
      }
      return `export default ${JSON.stringify(items)};\n`;
    },
  };
}

export default defineConfig({
  // Relative base keeps the built bundle servable from any path.
  base: "./",
  plugins: [galleryManifestPlugin()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: false,
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: false,
  },
});
