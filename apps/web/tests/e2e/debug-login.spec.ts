import { test } from "@playwright/test";

const BASE = "http://localhost:3000";

test("DEBUG: keyboard type + capture all network", async ({ page }) => {
  test.skip(process.env.E2E_DEBUG !== "1", "Diagnostic test; enable explicitly with E2E_DEBUG=1");
  const username = process.env.E2E_RESEARCHER_USERNAME;
  const password = process.env.E2E_RESEARCHER_PASSWORD;
  if (!username || !password) throw new Error("E2E researcher credentials are required");
  // Capture ALL responses
  const allResponses: { url: string; status: number }[] = [];
  page.on("response", async (r) => {
    allResponses.push({ url: r.url().replace("http://localhost:3000", ""), status: r.status() });
  });

  page.on("console", msg => {
    if (["error", "warn"].includes(msg.type())) console.log(`[${msg.type()}]`, msg.text().slice(0, 120));
  });

  await page.goto(`${BASE}/admin/login`, { waitUntil: "networkidle" });
  console.log("URL:", page.url());

  // Try keyboard type instead of fill
  const usernameInput = page.locator('[data-testid="input-username"]');
  const passwordInput = page.locator('[data-testid="input-password"]');

  await usernameInput.click();
  await page.keyboard.type(username, { delay: 50 });
  console.log("Typed username");

  await passwordInput.click();
  await page.keyboard.type(password, { delay: 50 });
  console.log("Typed password");

  // Check React state via evaluate
  const values = await page.evaluate(() => {
    const u = document.querySelector('[data-testid="input-username"]') as HTMLInputElement;
    const p = document.querySelector('[data-testid="input-password"]') as HTMLInputElement;
    return { usernameEntered: Boolean(u?.value), passwordEntered: Boolean(p?.value) };
  });
  console.log("Input state in DOM:", JSON.stringify(values));

  // Clear responses before submit to see only new ones
  allResponses.length = 0;

  // Submit via Enter key
  await page.keyboard.press("Enter");
  console.log("Pressed Enter");

  await page.waitForTimeout(10000);
  console.log("FINAL URL:", page.url());
  console.log("POST-SUBMIT responses:");
  allResponses.forEach(r => console.log(`  ${r.status} ${r.url}`));

  const cookies = await page.context().cookies("http://localhost:3000");
  console.log("COOKIES:", JSON.stringify(cookies.map(c => c.name)));

  const errorEl = await page.locator('[data-testid="error-message"]').textContent({ timeout: 500 }).catch(() => null);
  console.log("PAGE ERROR:", errorEl ?? "(none)");

  // Also try direct browser-side fetch to verify route works
  const fetchResult = await page.evaluate(async ({ username, password }) => {
    try {
      const r = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      return { status: r.status, ok: r.ok, body: await r.text() };
    } catch(e: unknown) {
      return { error: e instanceof Error ? e.message : "Unknown error" };
    }
  }, { username, password });
  console.log("DIRECT FETCH result:", JSON.stringify(fetchResult));
});
