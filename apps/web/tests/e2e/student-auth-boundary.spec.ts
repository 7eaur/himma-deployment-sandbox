import { expect, test } from "@playwright/test";

test.describe("Student authentication boundary", () => {
  test("logged-out visitors are redirected before protected student UI renders", async ({ page, context }) => {
    const protectedPaths = ["/student", "/student/session/999", "/student/activity/999"];

    for (const path of protectedPaths) {
      await context.clearCookies();
      await page.goto(path);
      await expect(page).toHaveURL(/\/student\/login\?next=/);

      const current = new URL(page.url());
      expect(current.pathname).toBe("/student/login");
      expect(current.searchParams.get("next")).toBe(path);
      await expect(page.locator('[data-testid="student-home"]')).toHaveCount(0);
      await expect(page.locator('[data-testid="activity-session"]')).toHaveCount(0);
    }
  });
});
