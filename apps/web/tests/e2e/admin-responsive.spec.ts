import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "admin-responsive");

async function login(page: Page) {
  if (!RESEARCHER_USERNAME || !RESEARCHER_PASSWORD) throw new Error("E2E researcher credentials are required");
  await page.goto("/admin/login");
  await page.getByTestId("input-username").fill(RESEARCHER_USERNAME);
  await page.getByTestId("input-password").fill(RESEARCHER_PASSWORD);
  await page.getByTestId("login-submit").click();
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });
}

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }));
  expect(metrics.documentWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.bodyWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
}

async function capture(page: Page, viewport: string, route: string) {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  const routeName = route === "/admin" ? "dashboard" : route.replace(/^\/admin\/?/, "").replaceAll("/", "-");
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `${viewport}-${routeName}.png`),
    fullPage: true,
  });
}

const ROUTES = [
  "/admin",
  "/admin/students",
  "/admin/students/new",
  "/admin/audio-review",
  "/admin/reports",
  "/admin/skill-reports",
  "/admin/settings",
];

for (const viewport of [
  { name: "phone-390x844", width: 390, height: 844 },
  { name: "small-tablet-768x1024", width: 768, height: 1024 },
]) {
  test(`admin shell and key pages stay usable without horizontal overlap on ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await login(page);

    for (const route of ROUTES) {
      await page.goto(route);
      await expect(page).not.toHaveURL(/\/admin\/login/);
      await expect(page.getByRole("button", { name: "فتح القائمة" })).toBeVisible();
      await expect(page.getByRole("button", { name: "الإشعارات" })).toBeVisible();
      await page.waitForTimeout(250);
      await expectNoHorizontalOverflow(page);
      await capture(page, viewport.name, route);
    }

    await page.goto("/admin/students");
    const studentLink = page.locator('a[href^="/admin/students/"]').filter({ hasNot: page.locator('a[href="/admin/students/new"]') }).first();
    if (await studentLink.isVisible().catch(() => false)) {
      const href = await studentLink.getAttribute("href");
      if (href && /^\/admin\/students\/\d+$/.test(href)) {
        await page.goto(href);
        await expect(page.getByRole("button", { name: "فتح القائمة" })).toBeVisible();
        await expectNoHorizontalOverflow(page);
        await capture(page, viewport.name, "student-detail");
      }
    }
  });
}