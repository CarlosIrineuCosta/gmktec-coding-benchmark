/**
 * Static file server for the built gallery.
 *
 * `npm run test:e2e` uses this as Playwright's webServer so the browser tests
 * are self-contained: it builds `dist/` if needed and then serves it on the
 * common preview/dev ports. Nothing here reaches the network — the only origins
 * involved are 127.0.0.1 and the files already inside `dist/`.
 */

import { spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIST = path.join(ROOT, "dist");
const VITE_BIN = path.join(ROOT, "node_modules", "vite", "bin", "vite.js");
const PORTS = (process.env.GALLERY_PORTS ?? "4173,5173,3000,8080")
  .split(",")
  .map((port) => Number.parseInt(port.trim(), 10))
  .filter(Boolean);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".map": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8"
};

if (!existsSync(path.join(DIST, "index.html"))) {
  console.log("dist/ not found — building first");
  const build = spawnSync(process.execPath, [VITE_BIN, "build"], { cwd: ROOT, stdio: "inherit" });
  if (build.status !== 0) process.exit(build.status ?? 1);
}

async function resolveFile(url) {
  const pathname = decodeURIComponent(new URL(url, "http://localhost").pathname);
  const candidates = pathname.endsWith("/") ? [`${pathname}index.html`] : [pathname, path.join(pathname, "index.html")];
  for (const candidate of candidates) {
    const absolute = path.join(DIST, path.normalize(candidate));
    if (!absolute.startsWith(DIST + path.sep)) continue; // refuse traversal
    try {
      const data = await readFile(absolute);
      return { data, type: MIME[path.extname(absolute).toLowerCase()] ?? "application/octet-stream" };
    } catch {
      /* try the next candidate */
    }
  }
  // Unknown route: fall back to the app shell.
  const index = path.join(DIST, "index.html");
  try {
    return { data: await readFile(index), type: MIME[".html"] };
  } catch {
    return null;
  }
}

const handler = async (request, response) => {
  const file = await resolveFile(request.url ?? "/");
  if (!file) {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("not found");
    return;
  }
  response.writeHead(200, {
    "content-type": file.type,
    "content-length": file.data.byteLength,
    "cache-control": "no-cache"
  });
  response.end(file.data);
};

for (const port of PORTS) {
  const server = createServer(handler);
  server.on("error", (error) => {
    if (error.code === "EADDRINUSE") {
      console.log(`port ${port} already in use — skipping`);
      return;
    }
    console.error(`port ${port} failed: ${error.message}`);
  });
  server.listen(port, () => console.log(`serving dist/ on http://127.0.0.1:${port}/`));
}
