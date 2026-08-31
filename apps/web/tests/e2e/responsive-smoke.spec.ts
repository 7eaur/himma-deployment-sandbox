import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const VIEWPORTS = [
  { name: "mobile-360x800", width: 360, height: 800 },
  { name: "mobile-390x844", width: 390, height: 844 },
  { name: "tablet-768x1024", width: 768, height: 1024 },
  { name: "tablet-landscape-1024x768", width: 1024, height: 768 },
  { name: "desktop-1440x900", width: 1440, height: 900 },
] as const;

const ROUTES = [
  { name: "landing", url: "/" },
  { name: "student-login", url: "/student/login" },
  { name: "supervisor-login", url: "/admin/login" },
] as const;

async function expectNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }));

  expect(metrics.documentWidth, `document overflow: ${JSON.stringify(metrics)}`).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.bodyWidth, `body overflow: ${JSON.stringify(metrics)}`).toBeLessThanOrEqual(metrics.innerWidth + 1);
}

test.describe("M04 responsive product smoke", () => {
  test("critical public and login surfaces fit the approved viewport matrix", async ({ page }) => {
    const screenshotDir = path.join(process.cwd(), "playwright-report", "responsive");
    await mkdir(screenshotDir, { recursive: true });

    for (const viewport of VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      for (const route of ROUTES) {
        await page.goto(route.url);
        await expect(page.locator("body")).toBeVisible();
        // Entry animations intentionally start from opacity 0. Capture the stable
        // product state, not an intermediate animation frame.
        await page.waitForTimeout(650);
        await expectNoHorizontalOverflow(page);

        await page.screenshot({
          path: path.join(screenshotDir, `${viewport.name}-${route.name}.png`),
          fullPage: true,
        });
      }
    }
  });

  test("mobile student login keeps its primary input and action touch-friendly", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/student/login");
    await page.waitForTimeout(650);

    const input = page.getByTestId("input-access-code");
    await expect(input).toBeVisible();
    const inputBox = await input.boundingBox();
    expect(inputBox?.height ?? 0).toBeGreaterThanOrEqual(44);

    const submit = page.getByRole("button").filter({ hasText: /دخول|ابدأ|متابعة/u }).first();
    await expect(submit).toBeVisible();
    const submitBox = await submit.boundingBox();
    expect(submitBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  });
});
