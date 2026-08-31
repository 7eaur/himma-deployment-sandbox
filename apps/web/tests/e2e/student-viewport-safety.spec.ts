import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function createStudent(page: Page, request: APIRequestContext, context: BrowserContext) {
  await loginSupervisor(request, context);
  await page.goto("/admin/students/new");
  await page.getByTestId("input-student-name").fill(`طالب فحص الشاشة ${Date.now()}`);
  await page.getByTestId("submit-create-student").click();
  const code = page.getByTestId("student-access-code");
  await expect(code).toBeVisible();
  const accessCode = (await code.textContent())?.trim() ?? "";
  await context.clearCookies();
  return accessCode;
}

async function loginStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function expectInsideViewport(page: Page, locator: ReturnType<Page["locator"]>) {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox();
  expect(box).toBeTruthy();
  const viewport = page.viewportSize();
  expect(viewport).toBeTruthy();
  if (!box || !viewport) return;
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 1);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 1);
  expect(box.width).toBeGreaterThanOrEqual(44);
  expect(box.height).toBeGreaterThanOrEqual(44);
}

async function expectNoHorizontalOverflow(page: Page) {
  const widths = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  expect(widths.document).toBeLessThanOrEqual(widths.viewport + 1);
  expect(widths.body).toBeLessThanOrEqual(widths.viewport + 1);
}

test.describe("student viewport safety", () => {
  test("assessment primary action is fully reachable at 1280x720", async ({ page, context, request }) => {
    test.setTimeout(90000);
    await page.setViewportSize({ width: 1280, height: 720 });
    const code = await createStudent(page, request, context);
    await loginStudent(request, context, code);

    const start = await request.post(`${API_URL}/assessment/start`, { data: { session_type: "pretest" } });
    expect(start.status()).toBe(200);
    const payload = await start.json();
    const sessionId = payload.id ?? payload.session_id;
    expect(sessionId).toBeTruthy();

    await page.goto(`/student/session/${sessionId}`);
    const root = page.getByTestId("assessment-session");
    await expect(root).toHaveAttribute("data-phase", "question", { timeout: 15000 });
    await expectNoHorizontalOverflow(page);

    const option = page.locator('button[aria-pressed="false"]').first();
    await expect(option).toBeVisible();
    await option.click();
    const cta = page.getByRole("button", { name: "تأكيد والمتابعة" });
    await expectInsideViewport(page, cta);

    const unresolved = await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll<HTMLElement>("*"));
      return all.some((element) => {
        const style = getComputedStyle(element);
        return [style.color, style.backgroundColor, style.borderColor].some((value) => /var\(/u.test(value));
      });
    });
    expect(unresolved).toBe(false);
  });
});
