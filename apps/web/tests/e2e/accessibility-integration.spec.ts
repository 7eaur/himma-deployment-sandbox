import { test, expect, APIRequestContext, BrowserContext, Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginAsSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
  const cookieMatch = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/);
  expect(cookieMatch?.[1]).toBeTruthy();
  await context.addCookies([{
    name: "access_token",
    value: cookieMatch?.[1] ?? "",
    domain: "localhost",
    path: "/",
    httpOnly: true,
    sameSite: "Lax",
    secure: false,
  }]);
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

async function expectDashboardReady(page: Page) {
  await expect(page.getByRole("heading", { name: /مرحبًا،/ })).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole("heading", { name: /ما الذي يحتاج انتباهك/ })).toBeVisible();
}

function channel(value: number) {
  const normalized = value / 255;
  return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string) {
  const value = hex.replace("#", "");
  const r = channel(Number.parseInt(value.slice(0, 2), 16));
  const g = channel(Number.parseInt(value.slice(2, 4), 16));
  const b = channel(Number.parseInt(value.slice(4, 6), 16));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string) {
  const first = luminance(a);
  const second = luminance(b);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

test.describe("M06 responsive and accessibility integration", () => {
  test("supervisor workspace is RTL, keyboard-focusable, and overflow-safe", async ({ page, context, request }) => {
    await loginAsSupervisor(request, context);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/admin");
    await expectDashboardReady(page);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expectNoHorizontalOverflow(page);

    await page.locator("body").press("Tab");
    const focusEvidence = await page.evaluate(() => {
      const active = document.activeElement as HTMLElement | null;
      if (!active) return null;
      const style = getComputedStyle(active);
      const rect = active.getBoundingClientRect();
      return {
        tag: active.tagName,
        outlineStyle: style.outlineStyle,
        outlineWidth: Number.parseFloat(style.outlineWidth),
        width: rect.width,
        height: rect.height,
      };
    });
    expect(focusEvidence).not.toBeNull();
    expect(["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"]).toContain(focusEvidence?.tag);
    expect(focusEvidence?.outlineStyle).not.toBe("none");
    expect(focusEvidence?.outlineWidth ?? 0).toBeGreaterThanOrEqual(3);
  });

  test("mobile supervisor navigation keeps touch targets and layout intact", async ({ page, context, request }) => {
    await loginAsSupervisor(request, context);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/admin");
    await expectDashboardReady(page);
    await expectNoHorizontalOverflow(page);

    const menu = page.getByRole("button", { name: "فتح القائمة" });
    await expect(menu).toBeVisible();
    const menuBox = await menu.boundingBox();
    expect(menuBox?.width ?? 0).toBeGreaterThanOrEqual(44);
    expect(menuBox?.height ?? 0).toBeGreaterThanOrEqual(44);

    await menu.click();
    const dialog = page.getByRole("dialog", { name: "قائمة لوحة المشرف" });
    await expect(dialog).toBeVisible();
    const firstNav = dialog.getByRole("link", { name: "نظرة عامة" });
    await expect(firstNav).toBeVisible();
    const navBox = await firstNav.boundingBox();
    expect(navBox?.height ?? 0).toBeGreaterThanOrEqual(44);
    await expectNoHorizontalOverflow(page);
    await page.screenshot({ path: "playwright-report/screenshots/18-mobile-supervisor-menu.png", fullPage: true });
  });

  test("reduced-motion preference suppresses decorative entry motion", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/student/login");
    await expect(page.getByRole("heading", { name: "مرحبًا يا بطل!" })).toBeVisible();
    const evidence = await page.locator(".student-login-card").evaluate((element) => {
      const style = getComputedStyle(element);
      const toMs = (value: string) => value.endsWith("ms") ? Number.parseFloat(value) : Number.parseFloat(value) * 1000;
      return {
        matches: matchMedia("(prefers-reduced-motion: reduce)").matches,
        animationMs: toMs(style.animationDuration),
        transitionMs: toMs(style.transitionDuration),
      };
    });
    expect(evidence.matches).toBe(true);
    expect(evidence.animationMs).toBeLessThanOrEqual(0.02);
    expect(evidence.transitionMs).toBeLessThanOrEqual(0.02);
  });

  test("200 percent zoom equivalent width remains usable", async ({ page, context, request }) => {
    await loginAsSupervisor(request, context);
    await page.setViewportSize({ width: 720, height: 900 });
    await page.goto("/admin");
    await expectDashboardReady(page);
    await expectNoHorizontalOverflow(page);
  });

  test("critical palette tokens meet normal-text contrast on light surfaces", async ({ page }) => {
    await page.goto("/");
    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        primary: style.getPropertyValue("--color-primary").trim(),
        green: style.getPropertyValue("--color-green").trim(),
        navy: style.getPropertyValue("--color-navy").trim(),
        background: style.getPropertyValue("--color-bg").trim(),
      };
    });
    expect(contrast(tokens.primary, "#FFFFFF")).toBeGreaterThanOrEqual(4.5);
    expect(contrast(tokens.green, "#FFFFFF")).toBeGreaterThanOrEqual(4.5);
    expect(contrast(tokens.navy, tokens.background)).toBeGreaterThanOrEqual(4.5);
  });

  test("child entry surfaces do not expose implementation vocabulary", async ({ page }) => {
    for (const route of ["/", "/student/login"]) {
      await page.goto(route);
      const body = (await page.locator("body").innerText()).toLowerCase();
      for (const forbidden of ["skill_id", "mapping_gap", "decision_id", "asr", "api", "postgres", "minio"]) {
        expect(body).not.toContain(forbidden);
      }
    }
  });
});