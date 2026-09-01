import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * Candidate-side verification of every observable clause in TASK.md.
 * The canonical contract in tests/gallery.spec.ts is left untouched; this
 * harness widens it so failures can be localised to a single criterion.
 */

const url = process.env.GALLERY_URL ?? "http://127.0.0.1:4173/";
const desktop = { width: 1440, height: 900 };
const mobile = { width: 390, height: 844 };

interface ManifestRow {
  id: string;
  creator: string;
  height: number;
  width: number;
  license: string;
  local_filename: string;
  source_page: string;
}

const manifest = JSON.parse(
  readFileSync(path.resolve(process.cwd(), "public/images.json"), "utf8"),
) as ManifestRow[];

interface Diagnostics {
  consoleErrors: string[];
  consoleWarnings: string[];
  pageErrors: string[];
  failedRequests: string[];
  badStatuses: string[];
  externalRequests: string[];
}

function watch(page: Page): Diagnostics {
  const diag: Diagnostics = {
    consoleErrors: [],
    consoleWarnings: [],
    pageErrors: [],
    failedRequests: [],
    badStatuses: [],
    externalRequests: [],
  };
  page.on("console", (message) => {
    if (message.type() === "error") {
      diag.consoleErrors.push(`error: ${message.text()}`);
    } else if (message.type() === "warning") {
      diag.consoleWarnings.push(`warning: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => diag.pageErrors.push(String(error)));
  page.on("requestfailed", (request) =>
    diag.failedRequests.push(`${request.method()} ${request.url()}`),
  );
  page.on("response", (response) => {
    const status = response.status();
    if (status >= 400) diag.badStatuses.push(`${status} ${response.url()}`);
    const host = new URL(response.url()).host;
    const ownHost = new URL(page.url() || url).host;
    if (host !== ownHost) diag.externalRequests.push(response.url());
  });
  return diag;
}

const tile = (page: Page, id: string): Locator =>
  page.locator(`.tile[data-id="${id}"]`);
const thumb = (page: Page, id: string): Locator => tile(page, id).locator("img");
const dialog = (page: Page): Locator => page.getByRole("dialog");
const activeInfo = (page: Page) =>
  page.evaluate(() => {
    const node = document.activeElement as HTMLElement | null;
    return node
      ? {
          tag: node.tagName.toLowerCase(),
          id: node.dataset?.id ?? "",
          label: node.getAttribute("aria-label") ?? "",
        }
      : null;
  });

test.describe("gallery contract", () => {
  test("1 + 7: every manifest image renders, cleanly, from local assets only", async ({
    page,
  }) => {
    const diag = watch(page);
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });

    await expect(page.locator(".tile")).toHaveCount(manifest.length);
    await expect(page.locator(".tile__image")).toHaveCount(manifest.length);

    for (const row of manifest) {
      const image = thumb(page, row.id);
      await expect(tile(page, row.id)).toBeVisible();
      await expect(image).toBeVisible();
      await expect(image).toHaveAttribute("alt", /\S/);
      const src = await image.getAttribute("src");
      expect(src ?? "").toContain(encodeURIComponent(row.local_filename));

      const caption = tile(page, row.id).locator(".tile__caption");
      expect(((await caption.innerText()) || "").trim().length).toBeGreaterThan(4);
      expect(await caption.innerText()).toContain(row.creator.split(" ").at(-1) as string);

      // Bytes actually arrived: decoded, non-zero, and not flagged broken.
      await expect
        .poll(
          () =>
            image.evaluate((node) => ({
              complete: (node as HTMLImageElement).complete,
              naturalWidth: (node as HTMLImageElement).naturalWidth,
              failed: node.closest(".tile")?.getAttribute("data-failed") === "true",
            })),
          { message: `${row.id} did not decode` },
        )
        .toEqual({ complete: true, naturalWidth: row.width, failed: false });
    }

    expect(diag.consoleErrors).toEqual([]);
    expect(diag.pageErrors).toEqual([]);
    expect(diag.failedRequests).toEqual([]);
    expect(diag.badStatuses).toEqual([]);
    expect(diag.externalRequests).toEqual([]);
    if (diag.consoleWarnings.length) console.log("console warnings:", diag.consoleWarnings);
    expect.soft(diag.consoleWarnings, "browser console warnings").toEqual([]);
  });

  test("2: portrait, landscape and square files keep their aspect ratio", async ({
    page,
  }) => {
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });
    const orientations = new Set<string>();

    for (const row of manifest) {
      const measured = await thumb(page, row.id).evaluate((node) => {
        const img = node as HTMLImageElement;
        const box = img.getBoundingClientRect();
        return { natural: img.naturalWidth / img.naturalHeight, rendered: box.width / box.height };
      });
      const declared = row.width / row.height;
      expect(measured.natural, row.id).toBeCloseTo(declared, 2);
      expect(measured.rendered, row.id).toBeCloseTo(measured.natural, 2);
      orientations.add(
        Math.abs(declared - 1) <= 0.02 ? "square" : declared > 1 ? "landscape" : "portrait",
      );
      expect(
        await tile(page, row.id).getAttribute("data-orientation"),
        row.id,
      ).toBe(Math.abs(declared - 1) <= 0.02 ? "square" : declared > 1 ? "landscape" : "portrait");
    }
    // The corpus really is mixed, so the check is meaningful.
    expect(orientations.size).toBeGreaterThanOrEqual(2);
  });

  test("3-5: lightbox opens with metadata, steps with buttons and arrows, closes on Escape", async ({
    page,
  }) => {
    const diag = watch(page);
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });

    const target = manifest[2]!;
    const opener = tile(page, target.id).locator("button.tile__trigger");
    await opener.focus();
    await page.keyboard.press("Enter"); // keyboard activation, not a mouse click

    await expect(dialog(page)).toBeVisible();
    await expect(dialog(page).locator(".lightbox__title")).not.toHaveText("");
    await expect(dialog(page).locator(".lightbox__caption")).not.toHaveText("");
    const metadata = dialog(page).locator(".lightbox__meta");
    await expect(metadata).toContainText(target.creator);
    await expect(metadata).toContainText(target.local_filename);
    await expect(metadata).toContainText(`${target.width}×${target.height}`);
    await expect(metadata).toContainText(/public domain/i);
    await expect(dialog(page).locator(".lightbox__source")).toHaveAttribute(
      "href",
      target.source_page,
    );
    await expect(dialog(page).locator(".lightbox__image")).toHaveAttribute("alt", /\S/);
    await expect(dialog(page).locator(".lightbox__status")).toContainText("3 of 12");
    expect(await activeInfo(page)).toMatchObject({ tag: "div" });

    const shownSrc = async (): Promise<string> =>
      (await dialog(page).locator(".lightbox__image").getAttribute("src")) ?? "";
    const shownIndex = async () =>
      Number(
        (await dialog(page).locator(".lightbox__status").innerText()).match(
          /(\d+)\s+of/,
        )?.[1] ?? -1,
      );

    await dialog(page).locator(".lightbox__nav--next").click();
    await expect
      .poll(async () => (await shownSrc()).includes(manifest[3]!.local_filename))
      .toBe(true);
    expect(await shownIndex()).toBe(4);

    await page.keyboard.press("ArrowRight");
    expect(await shownIndex()).toBe(5);
    expect(await shownSrc()).toContain(manifest[4]!.local_filename);

    await page.keyboard.press("ArrowLeft");
    await page.keyboard.press("ArrowLeft");
    expect(await shownIndex()).toBe(3);
    expect(await shownSrc()).toContain(target.local_filename);

    await dialog(page).locator(".lightbox__nav--prev").click();
    expect(await shownIndex()).toBe(2);

    // Wrap-around keeps stepping available in both directions.
    for (let i = 0; i < 2; i += 1) await page.keyboard.press("ArrowLeft");
    expect(await shownIndex()).toBe(12);

    // Focus stays inside the modal while it is open.
    for (let i = 0; i < 12; i += 1) await page.keyboard.press("Tab");
    const trapped = await page.evaluate(() =>
      document.querySelector(".lightbox")?.contains(document.activeElement ?? null),
    );
    expect(trapped).toBe(true);

    await page.keyboard.press("Escape");
    await expect(dialog(page)).toBeHidden();
    await expect
      .poll(() => page.evaluate(() => document.activeElement?.getAttribute("data-id")))
      .toBe(target.id);

    // Escape handed focus back to the very tile that opened the viewer.
    expect((await activeInfo(page))?.tag).toBe("button");
    expect(diag.consoleErrors).toEqual([]);
    expect(diag.pageErrors).toEqual([]);
  });

  test("5b: scrim click and close button both return focus", async ({ page }) => {
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });
    const opener = tile(page, manifest[0]!.id).locator("button.tile__trigger");
    await opener.click();
    await expect(dialog(page)).toBeVisible();
    await dialog(page).locator(".lightbox__close").click();
    await expect(dialog(page)).toBeHidden();
    await expect
      .poll(() => page.evaluate(() => document.activeElement?.getAttribute("data-id")))
      .toBe(manifest[0]!.id);

    await opener.click();
    await expect(dialog(page)).toBeVisible();
    await page.mouse.click(2, 2); // scrim, outside the panel
    await expect(dialog(page)).toBeHidden();
  });

  test("6: usable at 390px and 1440px, with reachable controls and no side scroll", async ({
    page,
  }) => {
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });
    const desktopOverflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      columns: getComputedStyle(document.querySelector(".gallery")!).columnCount,
    }));
    expect(desktopOverflow.scrollWidth).toBeLessThanOrEqual(desktopOverflow.clientWidth + 1);
    expect(Number(desktopOverflow.columns)).toBeGreaterThanOrEqual(3);

    await tile(page, manifest[1]!.id).locator("img").click();
    await expect(dialog(page)).toBeVisible();
    const desktopBox = await dialog(page).locator(".lightbox__panel").boundingBox();
    expect(desktopBox!.width).toBeLessThanOrEqual(desktop.width);
    expect(desktopBox!.height).toBeLessThanOrEqual(desktop.height);
    const nextBox = await dialog(page).locator(".lightbox__nav--next").boundingBox();
    expect(nextBox!.x + nextBox!.width).toBeLessThanOrEqual(desktop.width);
    await page.keyboard.press("Escape");

    await page.setViewportSize(mobile);
    await page.waitForTimeout(150);
    const mobileOverflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      columns: getComputedStyle(document.querySelector(".gallery")!).columnCount,
    }));
    expect(mobileOverflow.scrollWidth).toBeLessThanOrEqual(mobileOverflow.clientWidth + 1);
    expect(Number(mobileOverflow.columns)).toBe(1);

    for (const row of manifest) {
      const box = await thumb(page, row.id).boundingBox();
      expect(box, row.id).not.toBeNull();
      expect(box!.width).toBeGreaterThan(200);
      expect(box!.x).toBeGreaterThanOrEqual(-1);
      expect(box!.x + box!.width).toBeLessThanOrEqual(mobile.width + 1);
    }

    await tile(page, manifest[2]!.id).locator("img").click();
    await expect(dialog(page)).toBeVisible();
    const panel = await dialog(page).locator(".lightbox__panel").boundingBox();
    expect(panel!.width).toBeLessThanOrEqual(mobile.width + 1);
    expect(panel!.height).toBeLessThanOrEqual(mobile.height + 1);
    const image = await dialog(page).locator(".lightbox__image").boundingBox();
    expect(image!.width).toBeLessThanOrEqual(mobile.width + 1);
    for (const selector of [".lightbox__nav--prev", ".lightbox__nav--next", ".lightbox__close"]) {
      const box = await dialog(page).locator(selector).boundingBox();
      expect(box, selector).not.toBeNull();
      expect(box!.width, selector).toBeGreaterThanOrEqual(44);
      expect(box!.height, selector).toBeGreaterThanOrEqual(44);
      expect(box!.x, selector).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width, selector).toBeLessThanOrEqual(mobile.width);
      expect(box!.y + box!.height, selector).toBeLessThanOrEqual(mobile.height);
    }
    await page.keyboard.press("ArrowRight");
    await expect(dialog(page).locator(".lightbox__status")).toContainText("4 of 12");
    await page.keyboard.press("Escape");
    await expect(dialog(page)).toBeHidden();
  });

  test("6b: screenshots for visual review at both viewports", async ({ page }) => {
    await page.setViewportSize(desktop);
    await page.goto(url, { waitUntil: "load" });
    await expect(page.locator(".tile")).toHaveCount(manifest.length);
    await page.screenshot({ path: "artifacts/candidate-desktop.png", fullPage: true });
    await tile(page, manifest[0]!.id).locator("img").click();
    await expect(dialog(page)).toBeVisible();
    await page.screenshot({ path: "artifacts/candidate-lightbox-desktop.png" });
    await page.keyboard.press("Escape");
    await page.setViewportSize(mobile);
    await page.waitForTimeout(150);
    await page.screenshot({ path: "artifacts/candidate-mobile.png", fullPage: true });
    await tile(page, manifest[1]!.id).locator("img").click();
    await expect(dialog(page)).toBeVisible();
    await page.screenshot({ path: "artifacts/candidate-lightbox-mobile.png" });
  });
});
