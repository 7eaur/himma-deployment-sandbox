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
  await expect(page.getByTestId("input-student-name")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("input-student-name").fill(`طالب تجربة القبلي ${Date.now()}`);
  await page.getByTestId("submit-create-student").click();
  const code = page.getByTestId("student-access-code");
  await expect(code).toBeVisible({ timeout: 10000 });
  const accessCode = (await code.textContent())?.trim() ?? "";
  expect(accessCode).toMatch(/^\d{6}$/);
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

async function visibleAnswerButtons(page: Page) {
  const buttons = page.locator("main section button");
  const visible = [];
  for (let index = 0; index < await buttons.count(); index += 1) {
    const button = buttons.nth(index);
    const text = ((await button.textContent()) ?? "").trim();
    if (!(await button.isVisible()) || !(await button.isEnabled())) continue;
    if (/^(استمع|استمع\.\.\.|تأكيد والمتابعة|إعادة الترتيب|إعادة التسجيل|إرسال التسجيل)$/u.test(text)) continue;
    visible.push(button);
  }
  return visible;
}

async function answerVisibleChoice(page: Page) {
  const imageGroup = page.getByTestId("image-options");
  const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });
  if (await imageGroup.count()) {
    await imageGroup.getByRole("button").first().click();
  } else {
    const pressedOptions = page.locator('button[aria-pressed="false"]');
    if (await pressedOptions.count()) {
      await pressedOptions.first().click();
    } else {
      for (let guard = 0; guard < 12 && !(await confirm.isEnabled()); guard += 1) {
        const candidates = await visibleAnswerButtons(page);
        if (!candidates.length) break;
        await candidates[0].click();
      }
    }
  }
  await expect(confirm).toBeEnabled();
  await confirm.click();
}

async function assertQuestionHierarchy(page: Page) {
  const root = page.getByTestId("assessment-session");
  await expect(root).toHaveAttribute("data-phase", /^(question|submitting)$/);
  const heading = root.getByTestId("question-title");
  await expect(heading).toBeVisible();
  expect(((await heading.textContent()) ?? "").trim().length).toBeGreaterThan(10);
  const headingBox = await heading.boundingBox();
  const imageGroup = page.getByTestId("image-options");
  const pressedOptions = page.locator('button[aria-pressed="false"]');
  let firstAnswer;
  if (await imageGroup.count()) firstAnswer = imageGroup.getByRole("button").first();
  else if (await pressedOptions.count()) firstAnswer = pressedOptions.first();
  else {
    const candidates = await visibleAnswerButtons(page);
    expect(candidates.length).toBeGreaterThan(0);
    firstAnswer = candidates[0];
  }
  await expect(firstAnswer).toBeVisible();
  const answerBox = await firstAnswer.boundingBox();
  expect(headingBox).toBeTruthy();
  expect(answerBox).toBeTruthy();
  if (headingBox && answerBox) expect(answerBox.y).toBeGreaterThan(headingBox.y + headingBox.height - 2);
}

test.describe("approved pretest question experience", () => {
  test("first readiness questions use the approved copy and responsive template", async ({ page, context, request }) => {
    test.setTimeout(140000);
    const accessCode = await createStudent(page, request, context);
    await loginStudent(request, context, accessCode);
    const start = await request.post(`${API_URL}/assessment/start`, { data: { session_type: "pretest" } });
    expect([200, 409]).toContain(start.status());
    const startPayload = await start.json().catch(() => null);
    let sessionId = startPayload?.id ?? startPayload?.session_id;
    if (!sessionId) {
      await page.goto("/student");
      const button = page.getByRole("button", { name: "ابدأ الاختبار" });
      await expect(button).toBeEnabled();
      await button.click();
      sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    }
    expect(sessionId).toBeTruthy();

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`/student/session/${sessionId}`);
    for (let index = 0; index < 10; index += 1) {
      const root = page.getByTestId("assessment-session");
      await expect(root).toHaveAttribute("data-phase", "question", { timeout: 15000 });
      await assertQuestionHierarchy(page);

      if (index === 0) {
        await expect(root.getByTestId("question-title")).toHaveText("اضغط على الحرف التالي.");
        await expect(root.getByTestId("question-stimulus")).toHaveText("ب");
        await expect(root.getByText("تمييز الحرف بصريًا", { exact: true })).toBeVisible();
        await page.screenshot({ path: "playwright-report/screenshots/pretest-q1-desktop.png", fullPage: true });
        await page.setViewportSize({ width: 390, height: 844 });
        await expect(root.getByTestId("question-title")).toBeVisible();
        await expect(root.getByRole("button", { name: "تأكيد والمتابعة" })).toBeVisible();
        await page.screenshot({ path: "playwright-report/screenshots/pretest-q1-mobile.png", fullPage: true });
        await page.setViewportSize({ width: 1440, height: 900 });
      }
      if (index === 2) {
        await expect(root.getByTestId("question-title")).toHaveText("انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.");
        await expect(root.getByTestId("question-stimulus")).toHaveText("م");
        expect(await page.locator('button[aria-pressed="false"]').count()).toBeGreaterThanOrEqual(4);
        await expect(root.getByText("مـ", { exact: true })).toBeVisible();
      }
      if (index === 4) {
        const text = (await root.getByTestId("question-title").textContent()) ?? "";
        expect(text).toContain("الصورة");
        expect(text).toContain("يبدأ اسمها");
      }
      if (index === 6) {
        const text = (await root.getByTestId("question-title").textContent()) ?? "";
        expect(text).toContain("تنتهي به");
      }
      await answerVisibleChoice(page);
    }
  });
});
