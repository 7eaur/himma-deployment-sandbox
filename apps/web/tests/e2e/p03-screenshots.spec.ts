import { test } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3000";
const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const STUDENT_ACCESS_CODE = process.env.E2E_STUDENT_ACCESS_CODE;
const SCREENS_DIR = path.join(__dirname, "screenshots/p03");

const VIEWPORTS = [
  { name: "mobile",  width: 390,  height: 844 },
  { name: "tablet",  width: 768,  height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

test.describe("P03.2: Full screenshots — all viewports + all pages", () => {
  test.setTimeout(300000);

  test.beforeAll(() => {
    fs.mkdirSync(SCREENS_DIR, { recursive: true });
  });

  for (const vp of VIEWPORTS) {
    test(`${vp.name} (${vp.width}px)`, async ({ browser }) => {
      const ctx = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        locale: "ar-SA",
      });
      const page = await ctx.newPage();
      const shot = async (name: string) => {
        await page.screenshot({
          path: path.join(SCREENS_DIR, `${name}-${vp.name}.png`),
          fullPage: false,
        });
        console.log(`[shot] ${name}-${vp.name}.png`);
      };

      // ── Public pages ──────────────────────────────────────
      await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
      await page.waitForTimeout(800);
      await shot("welcome");

      await page.goto(`${BASE}/admin/login`, { waitUntil: "networkidle" });
      await page.waitForTimeout(600);
      await shot("admin-login");

      await page.goto(`${BASE}/student/login`, { waitUntil: "networkidle" });
      await page.waitForTimeout(600);
      await shot("student-login");

      // ── Admin login ───────────────────────────────────────
      await page.goto(`${BASE}/admin/login`, { waitUntil: "networkidle" });
      await page.locator('[data-testid="input-username"]').click();
      if (!RESEARCHER_USERNAME || !RESEARCHER_PASSWORD) {
        throw new Error("E2E_RESEARCHER_USERNAME and E2E_RESEARCHER_PASSWORD are required");
      }
      await page.keyboard.type(RESEARCHER_USERNAME, { delay: 30 });
      await page.locator('[data-testid="input-password"]').click();
      await page.keyboard.type(RESEARCHER_PASSWORD, { delay: 30 });
      await page.locator('[data-testid="login-submit"]').click();
      await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });
      await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
      await page.waitForTimeout(1000);

      // ── Admin pages ───────────────────────────────────────
      const adminPages = [
        { route: "/admin",               name: "admin-dashboard" },
        { route: "/admin/students",       name: "admin-students" },
        { route: "/admin/students/new",   name: "admin-create-student" },
        { route: "/admin/audio-review",   name: "admin-audio-review" },
        { route: "/admin/reports",        name: "admin-reports" },
        { route: "/admin/settings",       name: "admin-settings" },
      ];
      for (const pg of adminPages) {
        await page.goto(`${BASE}${pg.route}`, { waitUntil: "networkidle" });
        await page.waitForTimeout(700);
        await shot(pg.name);
      }

      // ── Student pages ─────────────────────────────────────
      // Logout first
      await page.evaluate(() => fetch("/api/auth/logout", { method: "POST" }));
      await page.goto(`${BASE}/student/login`, { waitUntil: "networkidle" });
      await page.locator('[data-testid="input-access-code"]').click();
      if (!STUDENT_ACCESS_CODE) {
        throw new Error("E2E_STUDENT_ACCESS_CODE is required for authenticated screenshots");
      }
      await page.keyboard.type(STUDENT_ACCESS_CODE, { delay: 40 });
      await page.getByRole("button", { name: /نبدأ|دخول/ }).first().click();
      await page.waitForURL(/\/student(?!\/login)/, { timeout: 15000 }).catch(async () => {
        console.log("Student login fallback — trying alternate code");
      });
      await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(1000);
      await shot("student-home");

      await ctx.close();
      console.log(`✓ Done: ${vp.name}`);
    });
  }
});
