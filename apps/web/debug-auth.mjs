import { chromium } from '@playwright/test';

const username = process.env.E2E_RESEARCHER_USERNAME;
const password = process.env.E2E_RESEARCHER_PASSWORD;
if (!username || !password) {
  throw new Error('Set E2E_RESEARCHER_USERNAME and E2E_RESEARCHER_PASSWORD locally');
}

const browser = await chromium.launch();
const context = await browser.newContext();
const page = await context.newPage();
const requests = [];

page.on('response', (response) => {
  if (response.url().includes('/api/')) {
    requests.push({ url: response.url(), status: response.status() });
  }
});

await page.goto('http://localhost:3000/admin/login');
await page.locator('[data-testid="input-username"]').fill(username);
await page.locator('[data-testid="input-password"]').fill(password);
await page.locator('[data-testid="login-submit"]').click();
await page.waitForTimeout(3000);

console.log('Current URL:', page.url());
console.log('API calls:', JSON.stringify(requests, null, 2));
await browser.close();
