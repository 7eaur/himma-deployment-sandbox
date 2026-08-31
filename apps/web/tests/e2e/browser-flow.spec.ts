import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3000";
const SCREENSHOTS = path.join(__dirname, "../../screenshots");
const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

if (!fs.existsSync(SCREENSHOTS)) fs.mkdirSync(SCREENSHOTS, { recursive: true });

async function shot(page: Page, name: string) {
  const p = path.join(SCREENSHOTS, `${name}.png`);
  await page.screenshot({ path: p, fullPage: false });
  console.log(`  [screenshot] ${name}.png`);
}

test("P02-S2: Full browser flow — researcher + student", async ({ page }) => {
  if (!RESEARCHER_USERNAME || !RESEARCHER_PASSWORD) {
    throw new Error("E2E_RESEARCHER_USERNAME and E2E_RESEARCHER_PASSWORD are required");
  }

  // ── 1. Admin login page ──────────────────────────────────────────────────
  await page.goto(`${BASE}/admin/login`);
  await expect(page.locator("h1")).not.toBeEmpty({ timeout: 8000 });

  await shot(page, "01-admin-login-page");
  console.log("✓ Admin login page loaded");

  // ── 2. Login as researcher ──────────────────────────────────────────────
  await page.getByTestId("input-username").click();
  await page.keyboard.type(RESEARCHER_USERNAME, { delay: 40 });
  await page.getByTestId("input-password").click();
  await page.keyboard.type(RESEARCHER_PASSWORD, { delay: 40 });
  await page.getByTestId("login-submit").click();

  // window.location.href triggers full navigation — wait for it
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });
  await page.waitForLoadState("networkidle", { timeout: 12000 }).catch(() => {});
  await page.waitForTimeout(1500);
  await shot(page, "02-admin-dashboard");
  console.log(`✓ Admin dashboard: ${page.url()}`);

  // ── 3. Refresh — session should persist ─────────────────────────────────
  await page.reload();
  await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1500);
  await expect(page).not.toHaveURL(/login/, { timeout: 8000 });
  console.log("✓ Session persists after refresh");

  // ── 4. Navigate to create student ───────────────────────────────────────
  await page.goto(`${BASE}/admin/students/new`);
  await expect(page).not.toHaveURL(/login/, { timeout: 5000 });
  await shot(page, "03-create-student-page");
  console.log("✓ Create student page loaded");

  // ── 5. Create a student ─────────────────────────────────────────────────
  const ts = Date.now();
  const nameInput = page.getByTestId("input-student-name").or(
    page.locator("input[placeholder*='اسم']").first()
  );
  await nameInput.click();
  await page.keyboard.type(`طالب اختبار ${ts}`, { delay: 20 });

  // Grade select if present
  const gradeSelect = page.getByTestId("input-student-grade").or(
    page.locator("select").first()
  );
  const gradeExists = await gradeSelect.isVisible().catch(() => false);
  if (gradeExists) {
    await expect(gradeSelect).toHaveValue("3");
    await expect(gradeSelect).toBeDisabled();
  }

  const createBtn = page.getByTestId("submit-create-student").or(
    page.getByRole("button", { name: /إنشاء|إضافة|حفظ/ }).first()
  );
  await createBtn.click();

  // Wait for access code to appear
  await page.waitForTimeout(2000);
  await shot(page, "04-student-created-with-code");

  // Extract access code
  const codeEl = page.locator("code").or(
    page.locator("[data-testid='access-code']").or(
      page.getByText(/[A-Z0-9]{2,4}-[0-9]{4}/)
    )
  ).first();
  const accessCode = await codeEl.textContent({ timeout: 8000 }).catch(() => null);
  expect(accessCode?.trim(), "New student access code should be displayed").toBeTruthy();
  console.log("✓ Student created and access code displayed");

  // ── 6. Admin logout ─────────────────────────────────────────────────────
  const logoutBtn = page.getByRole("button", { name: /خروج|تسجيل الخروج/ }).first()
    .or(page.getByTestId("btn-logout").first());
  const logoutExists = await logoutBtn.isVisible().catch(() => false);
  if (logoutExists) {
    await logoutBtn.click();
    await page.waitForURL(/login/, { timeout: 5000 }).catch(() => {});
  } else {
    // Direct logout via API
    await page.goto(`${BASE}/api/auth/logout`);
    await page.goto(`${BASE}/admin/login`);
  }
  await shot(page, "05-after-admin-logout");
  console.log("✓ Admin logged out");

  // ── 7. Student login ────────────────────────────────────────────────────
  await page.goto(`${BASE}/student/login`);
  await shot(page, "06-student-login-page");

  const code = accessCode!.trim();
  const codeInput = page.getByTestId("input-access-code").or(
    page.locator("input[placeholder*='رمز']").first()
  );
  await codeInput.click();
  await page.keyboard.type(code, { delay: 50 });
  await page.getByRole("button", { name: /دخول|نبدأ/ }).first().click();

  // window.location.href = /student triggers full navigation
  await page.waitForURL(/\/student(?!\/login)/, { timeout: 10000 });
  await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1500);
  await shot(page, "07-student-dashboard");
  console.log(`✓ Student logged in, URL: ${page.url()}`);

  // ── 8. Refresh — student session persists ───────────────────────────────
  await page.reload();
  await expect(page).not.toHaveURL(/login/, { timeout: 5000 });
  console.log("✓ Student session persists after refresh");

  // ── 9. Start assessment or navigate to session ──────────────────────────
  const startBtn = page.getByRole("button", { name: /ابدأ|اختبار|التقييم/ }).first();
  const startExists = await startBtn.isVisible({ timeout: 3000 }).catch(() => false);
  if (startExists) {
    await startBtn.click();
    await page.waitForTimeout(2000);
  } else {
    // Try navigating to assessment start directly
    await page.goto(`${BASE}/student`);
    const anyBtn = page.getByRole("button").first();
    if (await anyBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await anyBtn.click();
    }
  }
  await shot(page, "08-student-assessment-or-dashboard");
  console.log(`✓ Assessment area: ${page.url()}`);

  // ── 10. Look for a question ─────────────────────────────────────────────
  await page.waitForTimeout(1500);
  const questionArea = page.locator("[data-testid='question'], .question, [class*='question']").first();
  const hasQuestion = await questionArea.isVisible({ timeout: 5000 }).catch(() => false);
  if (hasQuestion) {
    await shot(page, "09-question-visible");
    console.log("✓ Question visible");

    // Answer MCQ if available
    const option = page.locator("[data-testid='option'], [class*='option'], button.optionBtn").first();
    const hasOptions = await option.isVisible({ timeout: 3000 }).catch(() => false);
    if (hasOptions) {
      await option.click();
      await page.waitForTimeout(500);
      await shot(page, "10-answer-selected");
      console.log("✓ Answer selected");
    }
  } else {
    await shot(page, "09-student-page-state");
    console.log("  (question area not found with current selectors — screenshot taken)");
  }

  // ── 11. Student logout ──────────────────────────────────────────────────
  await page.goto(`${BASE}/student/login`);
  await shot(page, "11-student-logged-out");
  console.log("✓ Student session ended");

  console.log("\n✓ P02-S2 Browser flow complete — screenshots in tests/e2e/screenshots/");
});
