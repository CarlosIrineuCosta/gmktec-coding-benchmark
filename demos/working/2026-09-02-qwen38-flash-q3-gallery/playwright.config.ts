import { defineConfig } from "@playwright/test";

/**
 * The browser contract lives in tests/gallery.spec.ts. This config only supplies
 * the harness around it: a self-contained static server for the built bundle and
 * the two viewports the task calls out (390 px mobile, 1440 px desktop).
 *
 * Set GALLERY_SKIP_WEBSERVER=1 when a server is already running elsewhere, or
 * PLAYWRIGHT_BASE_URL to point the tests at a different local origin.
 */
const PORT = Number.parseInt(process.env.GALLERY_PORT ?? "4173", 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${PORT}/`;
const skipServer = process.env.GALLERY_SKIP_WEBSERVER === "1";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  use: {
    screenshot: "off",
    baseURL
  },
  webServer: skipServer
    ? undefined
    : {
        command: "node scripts/serve-dist.mjs",
        url: baseURL,
        reuseExistingServer: true,
        timeout: 120_000,
        stdout: "pipe",
        stderr: "pipe"
      },
  projects: [
    {
      name: "desktop-1440",
      use: { viewport: { width: 1440, height: 900 } }
    },
    {
      name: "mobile-390",
      use: { viewport: { width: 390, height: 844 } }
    }
  ]
});
