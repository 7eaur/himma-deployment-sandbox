import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: "list",
  timeout: 120000, // 2 minutes per test — needed for 30 questions

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    locale: "ar-SA",
    // Allow cross-origin cookies to be sent (needed for API on :8000 and UI on :3000)
    extraHTTPHeaders: {},
  },

  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: [
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--disable-web-security",  // allow cross-origin cookies in test
          ],
        },
      },
    },
  ],

  // Next.js dev server — reuses the one started manually in terminal
  // Start it first: cd apps/web && set NEXT_PUBLIC_API_URL=http://localhost:8000 && npm run dev
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60000,
    env: { NEXT_PUBLIC_API_URL: "http://localhost:8000" },
  },
});
