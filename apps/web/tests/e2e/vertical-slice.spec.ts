import { test, expect, APIRequestContext, Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

type RichItem = {
  id: number;
  canonical_id?: string;
  interaction_type: string;
  steps: Array<{
    id: number;
    options: Array<{ id: number; text: string; order_index: number }>;
    assets?: Array<{ asset_id: string; asset_type: string; option_id?: number | null }>;
    media_gaps?: Array<Record<string, unknown>>;
  }>;
};

type ActivityPayload = {
  item: {
    id: number;
    canonical_id?: string;
    interaction_type: string;
  };
  step: {
    id: number;
    options: Array<{ id: number; text: string; order_index: number }>;
    assets?: Array<{ asset_id: string; asset_type: string; option_id?: number | null }>;
    media_gaps?: Array<Record<string, unknown>>;
  };
};

async function loginAsSupervisor(request: APIRequestContext, context: import("@playwright/test").BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status(), "Supervisor login should return 200").toBe(200);
  const setCookieHeader = response.headers()["set-cookie"];
  const cookieMatch = setCookieHeader?.match(/access_token=([^;]+)/);
  if (cookieMatch) {
    await context.addCookies([{
      name: "access_token",
      value: cookieMatch[1],
      domain: "localhost",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
      secure: false,
    }]);
  }
}

async function loginAsStudent(
  request: APIRequestContext,
  context: import("@playwright/test").BrowserContext,
  accessCode: string,
) {
  const response = await request.post(`${API_URL}/auth/student-login`, {
    data: { access_code: accessCode },
  });
  expect(response.status(), `Student login with code ${accessCode} should return 200`).toBe(200);
  const setCookieHeader = response.headers()["set-cookie"];
  const cookieMatch = setCookieHeader?.match(/access_token=([^;]+)/);
  if (cookieMatch) {
    await context.addCookies([{
      name: "access_token",
      value: cookieMatch[1],
      domain: "localhost",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
      secure: false,
    }]);
  }
}

async function shot(page: Page, name: string) {
  await page.screenshot({ path: `playwright-report/screenshots/${name}.png`, fullPage: true });
}

async function waitForAssessmentQuestion(page: Page) {
  const root = page.getByTestId("assessment-session");
  await expect(root).toHaveAttribute(
    "data-phase",
    /^(question|waiting_audio_review|done|error)$/,
    { timeout: 20000 },
  );
  const phase = await root.getAttribute("data-phase");
  if (phase === "error") throw new Error((await root.textContent()) || "Assessment runtime error");
  return phase;
}

async function recordFromVisibleReadingUI(page: Page, submitLabel: RegExp) {
  const start = page.getByRole("button", { name: "بدء التسجيل" });
  await expect(start).toBeVisible({ timeout: 5000 });
  await start.click();
  await page.waitForTimeout(850);
  const stop = page.getByRole("button", { name: "إيقاف التسجيل" });
  await expect(stop).toBeVisible({ timeout: 5000 });
  await stop.click();
  const submit = page.getByRole("button", { name: submitLabel });
  await expect(submit).toBeEnabled({ timeout: 7000 });
  await submit.click();
}

async function answerAssessmentVisual(page: Page, item: RichItem) {
  const interaction = item.interaction_type;
  const step = item.steps[0];
  if (!step) throw new Error("Assessment item has no visible step");

  if (interaction === "read_aloud" || interaction === "timed_read_aloud") {
    await recordFromVisibleReadingUI(page, /إرسال التسجيل/);
    return;
  }

  if (interaction === "sequence" || interaction === "memory_sequence" || interaction === "path_sequence" || interaction === "build_word") {
    const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });
    const sequenceImages = page.getByTestId("sequence-image-options");
    if (await sequenceImages.count()) {
      while (!(await confirm.isEnabled())) {
        const next = sequenceImages.getByRole("button").filter({ visible: true }).first();
        if (!(await next.count())) break;
        await next.click();
      }
    } else {
      const orderedOptions = [...step.options].sort((a, b) => a.order_index - b.order_index);
      for (const option of orderedOptions) {
        if (await confirm.isEnabled()) break;
        const candidate = page.getByRole("button", { name: option.text, exact: true }).first();
        await expect(candidate).toBeVisible({ timeout: 5000 });
        if (await candidate.isEnabled()) await candidate.click();
      }
    }
    await expect(confirm).toBeEnabled({ timeout: 5000 });
    await confirm.click();
    return;
  }

  const imageGroup = page.getByTestId("image-options");
  if (await imageGroup.count()) {
    const imageButtons = imageGroup.getByRole("button");
    const count = await imageButtons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await imageButtons.nth(index).click();
  } else {
    const optionButtons = page.locator('button[aria-pressed="false"]');
    await expect(optionButtons.first()).toBeVisible({ timeout: 5000 });
    const count = await optionButtons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await optionButtons.nth(index).click();
  }
  await page.getByRole("button", { name: "تأكيد والمتابعة" }).click();
}

async function answerActivityVisual(page: Page, payload: ActivityPayload) {
  const interaction = payload.item.interaction_type;

  const gapButton = page.getByRole("button", { name: "متابعة دون احتساب الجولة" });
  if (await gapButton.count()) {
    await gapButton.click();
    return;
  }

  if (interaction === "read_aloud" || interaction === "timed_read_aloud") {
    await recordFromVisibleReadingUI(page, /إرسال التسجيل/);
    return;
  }

  if (interaction === "sequence" || interaction === "memory_sequence" || interaction === "path_sequence" || interaction === "build_word") {
    const orderedOptions = [...payload.step.options].sort((a, b) => a.order_index - b.order_index);
    for (const option of orderedOptions) {
      const candidate = page.getByRole("button", { name: option.text, exact: true }).first();
      if (await candidate.count()) await candidate.click();
    }
    await page.getByRole("button", { name: "تأكيد والمتابعة" }).click();
    return;
  }

  const imageGroup = page.getByTestId("activity-image-options");
  if (await imageGroup.count()) {
    const buttons = imageGroup.getByRole("button");
    const count = await buttons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  } else {
    const buttons = page.locator('button[aria-pressed="false"]');
    await expect(buttons.first()).toBeVisible({ timeout: 5000 });
    const count = await buttons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  }
  await page.getByRole("button", { name: "تأكيد والمتابعة" }).click();
}

function isActivityNextResponse(response: import("@playwright/test").Response, sessionId: string) {
  return response.request().method() === "GET" && response.url().endsWith(`/activities/session/${sessionId}/next`);
}

test.describe("Himma recovered vertical slice", () => {
  test("public UX → protected supervisor → rich assessment → adaptive learning → management evidence", async ({ page, context, request }) => {
    test.setTimeout(240000);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /اقرأ بثقة/ })).toBeVisible();
    await shot(page, "01-public-child-focused-landing");

    await page.goto("/admin");
    await expect(page).toHaveURL(/\/admin\/login/, { timeout: 7000 });
    await expect(page.getByRole("heading", { name: "مرحبًا بك" })).toBeVisible();
    await shot(page, "02-supervisor-login-protected");

    await loginAsSupervisor(request, context);
    await page.goto("/admin");
    await expect(page.getByText("لوحة المشرف").first()).toBeVisible({ timeout: 10000 });
    await shot(page, "03-supervisor-dashboard");

    await page.goto("/admin/students/new");
    await expect(page).not.toHaveURL(/login/, { timeout: 5000 });
    await expect(page.getByText("الصف الثالث الابتدائي")).toBeVisible();

    const studentName = `طالب تجريبي ${Date.now()}`;
    await page.getByTestId("input-student-name").fill(studentName);
    await page.getByTestId("submit-create-student").click();

    const codeEl = page.getByTestId("student-access-code");
    await expect(codeEl).toBeVisible({ timeout: 10000 });
    const accessCode = (await codeEl.textContent())?.trim() ?? "";
    expect(accessCode).toMatch(/^\d{6}$/);
    await shot(page, "04-student-created-numeric-code");

    const studentsResponse = await request.get(`${API_URL}/researcher/students`);
    expect(studentsResponse.status()).toBe(200);
    const students: Array<{ id: number; access_code: string; full_name: string }> = await studentsResponse.json();
    const createdStudent = students.find((candidate) => candidate.access_code === accessCode);
    expect(createdStudent?.full_name).toBe(studentName);
    const studentId = createdStudent?.id;
    expect(studentId).toBeTruthy();

    await context.clearCookies();
    await loginAsStudent(request, context, accessCode);
    await page.goto("/student");
    await expect(page.getByRole("heading", { name: /مرحبًا يا/ })).toBeVisible({ timeout: 10000 });
    await shot(page, "05-student-journey-dashboard");

    await page.getByRole("button", { name: "ابدأ الاختبار" }).click();
    await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
    const sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    expect(sessionId).toBeTruthy();

    let answered = 0;
    let capturedImageAssessment = false;
    let capturedReadingAssessment = false;
    while (answered < 30) {
      const phase = await waitForAssessmentQuestion(page);
      if (phase === "waiting_audio_review" || phase === "done") break;

      const currentResponse = await request.get(`${API_URL}/assessment/session/${sessionId}/next`);
      expect(currentResponse.status()).toBe(200);
      const current: RichItem | null = await currentResponse.json();
      expect(current).toBeTruthy();
      if (!current) break;

      if (!capturedImageAssessment && (current.interaction_type === "choose_image" || current.interaction_type === "listen_choose_image")) {
        const images = page.getByTestId("image-options").locator("img");
        await expect(images.first()).toBeVisible({ timeout: 7000 });
        expect(await images.count()).toBeGreaterThanOrEqual(2);
        await shot(page, "06-assessment-real-image-choice");
        capturedImageAssessment = true;
      }
      if (!capturedReadingAssessment && (current.interaction_type === "read_aloud" || current.interaction_type === "timed_read_aloud")) {
        await expect(page.getByTestId("reading-text")).toBeVisible();
        await shot(page, "07-assessment-reading-recording");
        capturedReadingAssessment = true;
      }

      await answerAssessmentVisual(page, current);
      answered += 1;
      if (answered < 30) await waitForAssessmentQuestion(page);
      if (answered === 1) {
        await page.reload();
        await waitForAssessmentQuestion(page);
      }
    }

    expect(answered).toBe(30);
    expect(capturedImageAssessment).toBe(true);
    expect(capturedReadingAssessment).toBe(true);
    await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "waiting_audio_review", { timeout: 20000 });
    await shot(page, "08-assessment-waiting-audio-review");

    await context.clearCookies();
    await loginAsSupervisor(request, context);
    await page.goto("/admin/audio-review");
    const startReview = page.getByRole("button", { name: "بدء المراجعة" });
    await expect(startReview.first()).toBeVisible({ timeout: 15000 });
    let reviewed = 0;
    while (await startReview.count()) {
      await startReview.first().click();
      const save = page.getByRole("button", { name: "حفظ التقييم" });
      await expect(save).toBeEnabled();
      await save.click();
      reviewed += 1;
    }
    expect(reviewed).toBeGreaterThan(0);
    await shot(page, "09-audio-review-queue-cleared");

    await context.clearCookies();
    await loginAsStudent(request, context, accessCode);
    await page.goto(`/student/session/${sessionId}`);
    await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "done", { timeout: 20000 });
    await shot(page, "10-assessment-result");

    await page.goto("/student");
    const learningButton = page.getByRole("button", { name: /ابدأ أنشطة مستواك|متابعة الأنشطة/ });
    await expect(learningButton).toBeEnabled({ timeout: 10000 });
    const firstActivityResponsePromise = page.waitForResponse((response) => response.request().method() === "GET" && /\/activities\/session\/\d+\/next$/.test(response.url()), { timeout: 15000 });
    await learningButton.click();
    await expect(page).toHaveURL(/\/student\/activity\/\d+/, { timeout: 10000 });
    const learningSessionId = page.url().match(/\/student\/activity\/(\d+)/)?.[1];
    expect(learningSessionId).toBeTruthy();

    const firstActivityResponse = await firstActivityResponsePromise;
    expect(firstActivityResponse.status()).toBe(200);
    let current: ActivityPayload | null = await firstActivityResponse.json();
    expect(current).toBeTruthy();

    const activityRoot = page.getByTestId("activity-session");
    await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });
    await shot(page, "11-first-adaptive-learning-activity");

    let activityInteractions = 0;
    let capturedRichActivity = false;
    let adaptiveReviewHold = false;
    while ((await activityRoot.getAttribute("data-phase")) !== "done" && current) {
      activityInteractions += 1;
      expect(activityInteractions, "Adaptive learning path should terminate").toBeLessThan(100);

      if (!capturedRichActivity && (current.item.interaction_type.includes("image") || (current.step.assets ?? []).some((asset) => asset.asset_type === "image"))) {
        await shot(page, "12-adaptive-activity-real-media");
        capturedRichActivity = true;
      }

      const nextResponsePromise = page.waitForResponse((response) => isActivityNextResponse(response, learningSessionId!), { timeout: 8000 }).catch(() => null);
      await answerActivityVisual(page, current);
      await page.waitForTimeout(850);

      if ((await activityRoot.getAttribute("data-phase")) === "done") break;
      const nextResponse = await nextResponsePromise;
      if (!nextResponse) {
        await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 20000 });
        continue;
      }
      if (nextResponse.status() === 409) {
        const blocked = await nextResponse.json();
        expect(String(blocked?.detail || "")).toContain("ربط نشاط تقوية");
        adaptiveReviewHold = true;
        const hold = page.getByTestId("student-adaptive-hold");
        await expect(hold).toBeVisible({ timeout: 7000 });
        await expect(hold.getByRole("heading", { name: /نجهّز لك الخطوة الأنسب/ })).toBeVisible();
        await shot(page, "13-adaptive-review-hold");
        break;
      }
      expect(nextResponse.status()).toBe(200);
      current = await nextResponse.json();
      await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 20000 });
    }

    if (!adaptiveReviewHold) {
      await expect(page.getByText("أحسنت، أكملت أنشطة مستواك")).toBeVisible({ timeout: 15000 });
      await shot(page, "13-learning-complete");
    }

    await context.clearCookies();
    await loginAsSupervisor(request, context);

    const studentStateResponse = await request.get(`${API_URL}/researcher/students/${studentId}`);
    expect(studentStateResponse.status()).toBe(200);
    const studentState: {
      current_level: number;
      core_completed_items: number;
      core_total_items: number;
      core_completed: boolean;
      posttest_eligible: boolean;
    } = await studentStateResponse.json();

    await page.goto(`/admin/students/${studentId}`);
    await expect(page.getByRole("heading", { name: studentName })).toBeVisible({ timeout: 12000 });

    await page.getByRole("button", { name: "المسار والتقدم" }).click();
    await expect(
      page.getByText(`${studentState.core_completed_items} من ${studentState.core_total_items}`),
    ).toBeVisible({ timeout: 12000 });
    await expect(page.getByText(`المستوى ${studentState.current_level}`, { exact: true }).first()).toBeVisible();

    await page.getByRole("button", { name: "التقوية والتكيف" }).click();
    await expect(page.getByTestId("adaptation-panel")).toBeVisible();
    await expect(page.getByText("التعديل اليدوي لا يحذف القرار الآلي")).toBeVisible();

    // Academic contract: placement chooses a starting level, then the journey
    // continues through later levels before posttest. Promotion therefore opens
    // a fresh core session and current-level progress may correctly reset to 0/10.
    if (studentState.current_level < 3 || !studentState.core_completed) {
      expect(studentState.posttest_eligible).toBe(false);
    }

    await page.getByRole("button", { name: "الاختبارات" }).click();
    const posttestButton = page.getByRole("button", { name: /فتح الاختبار البعدي|إيقاف الإتاحة/ });
    if (studentState.posttest_eligible) {
      await expect(posttestButton).toBeEnabled();
    } else {
      await expect(posttestButton).toBeDisabled();
    }
    await shot(page, "14-supervisor-student-management-current-level");

    if (adaptiveReviewHold) {
      const panel = page.getByTestId("reinforcement-review-panel");
      await expect(panel).toBeVisible({ timeout: 10000 });
      await panel.getByRole("button", { name: "مراجعة القرار" }).click();
      await panel.getByLabel("سبب الإسناد").fill("اختيار نشاط تقوية معتمد لاستكمال المسار بعد مراجعة الأداء.");
      await panel.getByRole("button", { name: "اعتماد التقوية" }).click();
      await expect(page.getByText("تم إسناد نشاط التقوية. يستطيع الطالب الآن متابعة مساره.")).toBeVisible({ timeout: 8000 });
      await shot(page, "15-supervisor-reinforcement-assigned");

      await context.clearCookies();
      await loginAsStudent(request, context, accessCode);
      const resumedResponsePromise = page.waitForResponse((response) => response.request().method() === "GET" && /\/activities\/session\/\d+\/next$/.test(response.url()), { timeout: 15000 });
      await page.goto(`/student/activity/${learningSessionId}`);
      await expect(page.getByTestId("student-adaptive-hold")).toHaveCount(0, { timeout: 10000 });
      await expect(page.getByTestId("activity-session")).toHaveAttribute("data-phase", "active", { timeout: 15000 });
      const resumedResponse = await resumedResponsePromise;
      expect(resumedResponse.status()).toBe(200);
      const resumed: ActivityPayload | null = await resumedResponse.json();
      expect(resumed).toBeTruthy();
      await shot(page, "16-student-reinforcement-resumed");

      await context.clearCookies();
      await loginAsSupervisor(request, context);
    }

    await page.goto("/admin/reports");
    await expect(page.getByRole("heading", { name: "التقارير والإحصائيات" })).toBeVisible();
    await expect(page.getByText(studentName)).toBeVisible();
    await shot(page, adaptiveReviewHold ? "17-supervisor-live-reports" : "15-supervisor-live-reports");

    await page.goto("/admin/students");
    await expect(page.getByText(studentName)).toBeVisible({ timeout: 5000 });
  });
});