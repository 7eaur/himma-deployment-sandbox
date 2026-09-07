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

type LearningExperiencePayload = {
  item_id: number;
  stable_key: string;
  interaction_type: string;
  audio_review_status?: string | null;
  awaiting_audio_review?: boolean;
  step: {
    id: number;
    options: Array<{ id: number; text: string; order_index: number }>;
    assets?: Array<{ asset_id: string; asset_type: string; option_id?: number | null }>;
    media_gaps?: Array<Record<string, unknown>>;
  };
};

type ActivityPhase = "active" | "activity_complete" | "adaptive_hold" | "done" | "error";

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
  const start = page.getByTestId("record-reading");
  await expect(start).toBeVisible({ timeout: 5000 });
  await expect(start).toHaveAttribute("aria-label", "بدء التسجيل");
  await start.click();
  await page.waitForTimeout(850);
  const stop = page.getByTestId("record-reading");
  await expect(stop).toBeVisible({ timeout: 5000 });
  await expect(stop).toHaveAttribute("aria-label", "إيقاف التسجيل");
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

async function reviewPendingAssessmentAudio(
  page: Page,
  context: import("@playwright/test").BrowserContext,
  request: APIRequestContext,
  accessCode: string,
  assessmentSessionId: string,
  captureEvidence: boolean,
) {
  const root = page.getByTestId("assessment-session");
  await expect(root).toHaveAttribute("data-phase", "waiting_audio_review", { timeout: 10000 });
  await expect(page.getByText(/سيُراجع المشرف القراءة/)).toBeVisible();
  if (captureEvidence) await shot(page, "08-assessment-waiting-audio-review");

  await context.clearCookies();
  await loginAsSupervisor(request, context);
  await page.goto("/admin/audio-review");
  const startReview = page.getByRole("button", { name: "بدء المراجعة" });
  await expect(startReview.first()).toBeVisible({ timeout: 15000 });
  await startReview.first().click();
  const save = page.getByRole("button", { name: "حفظ التقييم" });
  await expect(save).toBeEnabled({ timeout: 7000 });
  await save.click();
  if (captureEvidence) await shot(page, "09-assessment-audio-reviewed-inline");

  await context.clearCookies();
  await loginAsStudent(request, context, accessCode);
  await page.goto(`/student/session/${assessmentSessionId}`);
  return waitForAssessmentQuestion(page);
}

async function chooseOrderedActivityItems(page: Page, payload: LearningExperiencePayload) {
  const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });
  const imageGroup = page.getByTestId("activity-sequence-image-options");
  if (await imageGroup.count()) {
    const orderedOptions = [...payload.step.options].sort((a, b) => a.order_index - b.order_index);
    for (const option of orderedOptions) {
      if (await confirm.isEnabled()) break;
      const candidate = imageGroup.getByRole("button", { name: new RegExp(option.text) }).first();
      if (await candidate.count()) await candidate.click();
      else {
        const remaining = imageGroup.getByRole("button").first();
        if (await remaining.count()) await remaining.click();
      }
    }
  } else {
    const orderedOptions = [...payload.step.options].sort((a, b) => a.order_index - b.order_index);
    for (const option of orderedOptions) {
      if (await confirm.isEnabled()) break;
      const candidate = page.getByRole("button", { name: option.text, exact: true }).first();
      if (await candidate.count()) await candidate.click();
    }
  }
  await expect(confirm).toBeEnabled({ timeout: 5000 });
  await confirm.click();
}

async function answerActivityVisual(page: Page, payload: LearningExperiencePayload) {
  const interaction = payload.interaction_type;
  expect(
    payload.step.media_gaps ?? [],
    `Approved journey reached a blocked media gap for item ${payload.stable_key || payload.item_id}`,
  ).toEqual([]);

  if (interaction === "read_aloud" || interaction === "timed_read_aloud") {
    await recordFromVisibleReadingUI(page, /إرسال التسجيل/);
    return;
  }

  if (interaction === "memory_sequence") {
    const preview = page.getByTestId("activity-memory-preview");
    if (await preview.count()) {
      await expect(preview).toBeVisible({ timeout: 5000 });
      await page.getByRole("button", { name: "التالي", exact: true }).click();
      await expect(page.getByTestId("activity-sequence-image-options")).toBeVisible({ timeout: 5000 });
    }
    await chooseOrderedActivityItems(page, payload);
    return;
  }

  if (interaction === "sequence" || interaction === "build_word") {
    await chooseOrderedActivityItems(page, payload);
    return;
  }

  if (interaction === "path_sequence") {
    throw new Error(`Retired path_sequence reached student runtime: ${payload.stable_key || payload.item_id}`);
  }

  const imageGroup = page.getByTestId("activity-image-options");
  if (await imageGroup.count()) {
    const buttons = imageGroup.getByTestId("activity-option");
    const count = await buttons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  } else {
    const buttons = page.getByTestId("activity-option");
    await expect(buttons.first()).toBeVisible({ timeout: 5000 });
    const count = await buttons.count();
    const selections = interaction === "choose_many" || interaction === "listen_choose_many" ? Math.min(2, count) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  }
  await page.getByRole("button", { name: "تأكيد والمتابعة" }).click();
}

async function waitForActivityPayload(page: Page, payload: LearningExperiencePayload) {
  const root = page.getByTestId("activity-session");
  await expect(root).toHaveAttribute("data-phase", "active", { timeout: 20000 });
  await expect(root).toHaveAttribute("data-item-id", String(payload.item_id), { timeout: 20000 });
  await expect(root).toHaveAttribute("data-step-id", String(payload.step.id), { timeout: 20000 });
  await expect(root).toHaveAttribute("data-interaction-type", payload.interaction_type, { timeout: 20000 });
  await expect(root).toHaveAttribute("data-media-gap-count", "0", { timeout: 20000 });
}

async function waitForActivityPhase(page: Page): Promise<ActivityPhase> {
  const root = page.getByTestId("activity-session");
  await expect(root).toHaveAttribute("data-phase", /^(active|activity_complete|adaptive_hold|done|error)$/, { timeout: 20000 });
  const phase = (await root.getAttribute("data-phase")) as ActivityPhase;
  if (phase === "error") throw new Error((await root.textContent()) || "Learning runtime error");
  return phase;
}

async function fetchLearningExperience(
  request: APIRequestContext,
  sessionId: string,
): Promise<LearningExperiencePayload | null> {
  const response = await request.get(`${API_URL}/learning-experience/session/${sessionId}`);
  expect(response.status(), "Authoritative learning-experience payload should return 200").toBe(200);
  return response.json();
}

async function reviewPendingLearningAudio(
  page: Page,
  context: import("@playwright/test").BrowserContext,
  request: APIRequestContext,
  accessCode: string,
  learningSessionId: string,
) {
  await expect(page.getByTestId("student-audio-review-hold")).toHaveCount(0, { timeout: 10000 });

  await context.clearCookies();
  await loginAsSupervisor(request, context);
  await page.goto("/admin/audio-review");
  const startReview = page.getByRole("button", { name: "بدء المراجعة" });
  await expect(startReview.first()).toBeVisible({ timeout: 15000 });
  await startReview.first().click();
  const save = page.getByRole("button", { name: "حفظ التقييم" });
  await expect(save).toBeEnabled({ timeout: 7000 });
  await save.click();

  await context.clearCookies();
  await loginAsStudent(request, context, accessCode);
  await page.goto(`/student/activity/${learningSessionId}`);
  await expect(page.getByTestId("student-audio-review-hold")).toHaveCount(0, { timeout: 10000 });
}

async function continueCelebration(page: Page): Promise<"continue" | "journey"> {
  await expect(page.getByText("إنجاز جديد")).toBeVisible({ timeout: 7000 });
  const next = page.getByRole("button", { name: "ابدأ النشاط التالي" });
  if (await next.count()) {
    await next.click();
    return "continue";
  }
  await expect(page.getByRole("button", { name: "العودة إلى مساري" })).toBeVisible();
  return "journey";
}

test.describe("Himma recovered vertical slice", () => {
  test("public UX → protected supervisor → resilient assessment → adaptive learning → management evidence", async ({ page, context, request }) => {
    test.setTimeout(360000);

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

    // A stale/dead assessment link must recover to the student's authoritative journey,
    // not trap the child on a useless retry loop.
    await page.goto("/student/session/999999999");
    await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "error", { timeout: 12000 });
    const recoveryButton = page.getByRole("button", { name: "العودة إلى مساري" });
    await expect(recoveryButton).toBeVisible();
    await recoveryButton.click();
    await expect(page).toHaveURL(/\/student$/, { timeout: 7000 });
    await expect(page.getByRole("heading", { name: /مرحبًا يا/ })).toBeVisible();

    await page.getByRole("button", { name: "ابدأ الاختبار" }).click();
    await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
    const sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    expect(sessionId).toBeTruthy();

    let answered = 0;
    let reviewedAssessmentAudio = 0;
    let capturedAssessmentReviewHold = false;
    let capturedImageAssessment = false;
    let capturedReadingAssessment = false;
    let capturedAudioControls = false;
    while (answered < 30) {
      const phase = await waitForAssessmentQuestion(page);
      if (phase === "done") break;
      expect(phase).toBe("question");

      const currentResponse = await request.get(`${API_URL}/assessment/session/${sessionId}/next`);
      expect(currentResponse.status()).toBe(200);
      const currentAssessment: RichItem | null = await currentResponse.json();
      expect(currentAssessment).toBeTruthy();
      if (!currentAssessment) break;

      if (!capturedImageAssessment && (currentAssessment.interaction_type === "choose_image" || currentAssessment.interaction_type === "listen_choose_image")) {
        const images = page.getByTestId("image-options").locator("img");
        await expect(images.first()).toBeVisible({ timeout: 7000 });
        expect(await images.count()).toBeGreaterThanOrEqual(2);
        await shot(page, "06-assessment-real-image-choice");
        capturedImageAssessment = true;
      }

      if (!capturedAudioControls && currentAssessment.interaction_type.startsWith("listen_")) {
        const listen = page.getByTestId("listen-prompt");
        await expect(listen).toHaveAttribute("aria-label", "استمع");
        await listen.click();
        await expect(listen).toHaveAttribute("aria-label", "إيقاف مؤقت", { timeout: 3000 });
        await listen.click();
        await expect(listen).toHaveAttribute("aria-label", "متابعة", { timeout: 3000 });
        await listen.click();
        await expect(listen).toHaveAttribute("aria-label", "إيقاف مؤقت", { timeout: 3000 });
        capturedAudioControls = true;
      }

      const readingRound = currentAssessment.interaction_type === "read_aloud" || currentAssessment.interaction_type === "timed_read_aloud";
      if (!capturedReadingAssessment && readingRound) {
        await expect(page.getByTestId("reading-text")).toBeVisible();
        await shot(page, "07-assessment-reading-recording");
        capturedReadingAssessment = true;
      }

      await answerAssessmentVisual(page, currentAssessment);
      answered += 1;

      if (readingRound) {
        const waitingPhase = await waitForAssessmentQuestion(page);
        expect(waitingPhase).toBe("waiting_audio_review");
        const resumedPhase = await reviewPendingAssessmentAudio(
          page,
          context,
          request,
          accessCode,
          sessionId!,
          !capturedAssessmentReviewHold,
        );
        capturedAssessmentReviewHold = true;
        reviewedAssessmentAudio += 1;
        if (answered < 30) expect(resumedPhase).toBe("question");
        continue;
      }

      if (answered < 30) await waitForAssessmentQuestion(page);
      if (answered === 1) {
        await page.reload();
        await waitForAssessmentQuestion(page);
      }
    }

    expect(answered).toBe(30);
    expect(reviewedAssessmentAudio).toBeGreaterThan(0);
    expect(capturedAssessmentReviewHold).toBe(true);
    expect(capturedImageAssessment).toBe(true);
    expect(capturedReadingAssessment).toBe(true);
    expect(capturedAudioControls).toBe(true);
    await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "done", { timeout: 20000 });
    await shot(page, "10-assessment-result");

    await page.goto("/student");
    const learningButton = page.getByRole("button", { name: /ابدأ أنشطة مستواك|متابعة الأنشطة/ });
    await expect(learningButton).toBeEnabled({ timeout: 10000 });
    await learningButton.click();
    await expect(page).toHaveURL(/\/student\/activity\/\d+/, { timeout: 10000 });
    const learningSessionId = page.url().match(/\/student\/activity\/(\d+)/)?.[1];
    expect(learningSessionId).toBeTruthy();

    let phase = await waitForActivityPhase(page);
    expect(phase).toBe("active");
    let current = await fetchLearningExperience(request, learningSessionId!);
    expect(current).toBeTruthy();
    await waitForActivityPayload(page, current!);
    await shot(page, "11-first-adaptive-learning-activity");

    let activityInteractions = 0;
    let capturedRichActivity = false;
    let capturedLearningAudio = false;
    let capturedActivityCelebration = false;
    let adaptiveReviewHold = false;
    let reachedJourneyBoundary = false;

    while (current && !reachedJourneyBoundary) {
      activityInteractions += 1;
      expect(activityInteractions, "Adaptive learning path should terminate").toBeLessThan(120);
      await waitForActivityPayload(page, current);

      if (!capturedRichActivity && (current.interaction_type.includes("image") || (current.step.assets ?? []).some((asset) => asset.asset_type === "image"))) {
        await shot(page, "12-adaptive-activity-real-media");
        capturedRichActivity = true;
      }

      const readingRound = current.interaction_type === "read_aloud" || current.interaction_type === "timed_read_aloud";
      await answerActivityVisual(page, current);
      phase = await waitForActivityPhase(page);

      if (phase === "activity_complete") {
        if (!capturedActivityCelebration) {
          await expect(page.getByText(/أنجزت جولات نشاط|تدرّبت بنجاح/)).toBeVisible();
          await shot(page, "13-activity-complete-celebration");
          capturedActivityCelebration = true;
        }
      }

      if (readingRound) {
        await expect(page.getByTestId("student-audio-review-hold")).toHaveCount(0, { timeout: 10000 });
        if (!capturedLearningAudio) {
          await shot(page, "14-learning-audio-continues-without-review-message");
          capturedLearningAudio = true;
        }
        await reviewPendingLearningAudio(page, context, request, accessCode, learningSessionId!);
        phase = await waitForActivityPhase(page);
        if (phase === "adaptive_hold") {
          adaptiveReviewHold = true;
          break;
        }
        if (phase === "done") {
          reachedJourneyBoundary = true;
          break;
        }
        if (phase === "activity_complete") {
          const next = await continueCelebration(page);
          if (next === "journey") {
            reachedJourneyBoundary = true;
            break;
          }
          phase = await waitForActivityPhase(page);
          if (phase === "adaptive_hold") {
            adaptiveReviewHold = true;
            break;
          }
          if (phase === "done") {
            reachedJourneyBoundary = true;
            break;
          }
        }
        if (phase === "active") current = await fetchLearningExperience(request, learningSessionId!);
        continue;
      }

      if (phase === "activity_complete") {
        const next = await continueCelebration(page);
        if (next === "journey") {
          reachedJourneyBoundary = true;
          break;
        }
        phase = await waitForActivityPhase(page);
      }

      if (phase === "adaptive_hold") {
        adaptiveReviewHold = true;
        const hold = page.getByTestId("student-adaptive-hold");
        await expect(hold).toBeVisible({ timeout: 7000 });
        await expect(hold.getByRole("heading", { name: /نجهّز لك الخطوة الأنسب/ })).toBeVisible();
        await shot(page, "15-adaptive-review-hold");
        break;
      }

      if (phase === "done") {
        reachedJourneyBoundary = true;
        break;
      }

      expect(phase).toBe("active");
      current = await fetchLearningExperience(request, learningSessionId!);
    }

    expect(capturedLearningAudio).toBe(true);
    expect(capturedActivityCelebration).toBe(true);

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
    await expect(page.getByText(`${studentState.core_completed_items} من ${studentState.core_total_items}`)).toBeVisible({ timeout: 12000 });
    await expect(page.getByText(`المستوى ${studentState.current_level}`, { exact: true }).first()).toBeVisible();

    await page.getByRole("button", { name: "التقوية والتكيف" }).click();
    await expect(page.getByTestId("adaptation-panel")).toBeVisible();
    await expect(page.getByText("التعديل اليدوي لا يحذف القرار الآلي")).toBeVisible();

    if (studentState.current_level < 3 || !studentState.core_completed) {
      expect(studentState.posttest_eligible).toBe(false);
    }

    await page.getByRole("button", { name: "الاختبارات" }).click();
    const posttestButton = page.getByRole("button", { name: /فتح الاختبار البعدي|إيقاف الإتاحة/ });
    if (studentState.posttest_eligible) await expect(posttestButton).toBeEnabled();
    else await expect(posttestButton).toBeDisabled();
    await shot(page, "16-supervisor-student-management-current-level");

    if (adaptiveReviewHold) {
      const panel = page.getByTestId("reinforcement-review-panel");
      await expect(panel).toBeVisible({ timeout: 10000 });
      await panel.getByRole("button", { name: "مراجعة القرار" }).click();
      await panel.getByLabel("سبب الإسناد").fill("اختيار نشاط تقوية معتمد لاستكمال المسار بعد مراجعة الأداء.");
      await panel.getByRole("button", { name: "اعتماد التقوية" }).click();
      await expect(page.getByText("تم إسناد نشاط التقوية. يستطيع الطالب الآن متابعة مساره.")).toBeVisible({ timeout: 8000 });
      await shot(page, "17-supervisor-reinforcement-assigned");

      await context.clearCookies();
      await loginAsStudent(request, context, accessCode);
      await page.goto(`/student/activity/${learningSessionId}`);
      await expect(page.getByTestId("student-adaptive-hold")).toHaveCount(0, { timeout: 10000 });
      await expect(page.getByTestId("activity-session")).toHaveAttribute("data-phase", "active", { timeout: 15000 });
      const resumed = await fetchLearningExperience(request, learningSessionId!);
      expect(resumed).toBeTruthy();
      await shot(page, "18-student-reinforcement-resumed");

      await context.clearCookies();
      await loginAsSupervisor(request, context);
    }

    await page.goto("/admin/reports");
    await expect(page.getByRole("heading", { name: "التقارير والإحصائيات" })).toBeVisible();
    await expect(page.getByRole("table").getByRole("link", { name: studentName, exact: true })).toBeVisible();
    await shot(page, adaptiveReviewHold ? "19-supervisor-live-reports" : "17-supervisor-live-reports");

    await page.goto("/admin/students");
    await expect(page.getByRole("table").getByRole("link", { name: studentName, exact: true })).toBeVisible({ timeout: 5000 });
  });
});
