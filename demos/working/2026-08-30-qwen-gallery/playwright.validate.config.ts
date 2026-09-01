import { defineConfig } from "@playwright/test";

/**
 * Candidate-side verification harness. Deliberately separate from `tests/`
 * (the graded contract) so the canonical spec stays untouched and runnable on
 * its own. Run it with:
 *   npx playwright test --config playwright.validate.config.ts
 */
export default defineConfig({
  testDir: "./validate",
  timeout: 60_000,
  reporter: [["list"]],
  use: {
    screenshot: "off",
    trace: "off",
    video: "off",
  },
});
