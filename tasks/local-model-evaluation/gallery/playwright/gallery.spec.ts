import { expect, test } from "@playwright/test";

const desktop = { width: 1440, height: 900 };
const mobile = { width: 390, height: 844 };

test("gallery is observable and keyboard-accessible", async ({ page }) => {
  await page.setViewportSize(desktop);
  await page.goto(process.env.GALLERY_URL!);
  const galleryImages = page.locator(".tile__image");
  await expect(galleryImages).toHaveCount(12);
  await expect(galleryImages.first()).toHaveAttribute("alt", /.+/);
  await galleryImages.first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await page.screenshot({ path: "artifacts/gallery-desktop.png", fullPage: true });
  await page.setViewportSize(mobile);
  await page.screenshot({ path: "artifacts/gallery-mobile.png", fullPage: true });
});
