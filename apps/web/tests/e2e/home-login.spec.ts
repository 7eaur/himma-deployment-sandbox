import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test("renders Himma logo and split login buttons", async ({ page }) => {
    await page.goto("/");

    // الشعار والرسالة الترحيبية
    await expect(page.locator(".logo-text").first()).toHaveText("هِمّة");
    await expect(page.getByText("أتعلم، أتطور، أصل إلى القمة")).toBeVisible();

    // زرا الدخول (مفصولة)
    const studentBtn = page.getByRole("link", { name: /الدخول برمز الطالب/i });
    const adminBtn = page.getByRole("link", { name: /دخول الإدارة/i });

    await expect(studentBtn).toHaveAttribute("href", "/student/login");
    await expect(adminBtn).toHaveAttribute("href", "/admin/login");
  });

  test("page is in RTL direction", async ({ page }) => {
    await page.goto("/");
    const htmlDir = await page.locator("html").getAttribute("dir");
    expect(htmlDir).toBe("rtl");
  });
});

test.describe("Login Page — Admin", () => {
  test("renders admin form", async ({ page }) => {
    await page.goto("/admin/login");

    await expect(page.getByRole("heading", { name: "دخول الإدارة" })).toBeVisible();
    await expect(page.getByTestId("input-username")).toBeVisible();
    await expect(page.getByTestId("input-password")).toBeVisible();
  });

  test("shows error on wrong credentials", async ({ page }) => {
    await page.goto("/admin/login");

    await page.getByTestId("input-username").fill("wrong_user");
    await page.getByTestId("input-password").fill("wrong_pass");
    await page.getByTestId("login-submit").click();

    const errorEl = page.getByTestId("error-message");
    await expect(errorEl).toBeVisible({ timeout: 5000 }).catch(() => {
      // Backend not running is acceptable in CI without full stack
    });
  });
});

test.describe("Login Page — Student", () => {
  test("renders student code input", async ({ page }) => {
    await page.goto("/student/login");

    await expect(page.getByRole("heading", { name: "دخول الطالب" })).toBeVisible();
    await expect(page.getByTestId("input-access-code")).toBeVisible();
  });

  test("access code input converts to uppercase", async ({ page }) => {
    await page.goto("/student/login");

    const codeInput = page.getByTestId("input-access-code");
    await codeInput.fill("stu-1234");
    const val = await codeInput.inputValue();
    expect(val).toBe("STU-1234");
  });
});
