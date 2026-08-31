import { mkdirSync } from "node:fs";
import { expect, test } from "@playwright/test";

test.describe("approved media fidelity", () => {
  test("serves real educational images and audio through the web proxy", async ({ page, request }) => {
    const imageResponse = await request.get("/api/media/VOC-01");
    expect(imageResponse.status()).toBe(200);
    expect(imageResponse.headers()["content-type"]).toContain("image/");
    expect((await imageResponse.body()).byteLength).toBeGreaterThan(1_000);

    const audioResponse = await request.get("/api/media/LET-01");
    expect(audioResponse.status()).toBe(200);
    expect(audioResponse.headers()["content-type"]).toContain("audio/");
    expect((await audioResponse.body()).byteLength).toBeGreaterThan(500);

    await page.goto("/");
    await page.setContent(`
      <main dir="rtl">
        <img id="approved-image" src="/api/media/VOC-01" alt="موزة" />
        <audio id="approved-audio" src="/api/media/LET-01"></audio>
      </main>
    `);

    const image = page.locator("#approved-image");
    await expect(image).toBeVisible();
    await expect.poll(async () => image.evaluate((element) => (element as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);

    const audio = page.locator("#approved-audio");
    await expect.poll(async () => audio.evaluate((element) => (element as HTMLMediaElement).readyState)).toBeGreaterThan(0);
  });

  test("renders every approved generated sequence scene and captures visual evidence", async ({ page, request }) => {
    const generated = [
      ["HIMMA-GEN-SEQ-001", "غسل اليدين"],
      ["HIMMA-GEN-SEQ-002", "الأكل"],
      ["HIMMA-GEN-SEQ-003", "فتح الكتاب"],
      ["HIMMA-GEN-SEQ-004", "سقي الزهرة"],
      ["HIMMA-GEN-SEQ-005", "لبس الحذاء"],
      ["HIMMA-GEN-SEQ-006", "الخروج من المنزل"],
      ["HIMMA-GEN-SEQ-007", "دخول المكتبة"],
      ["HIMMA-GEN-SEQ-008", "الذهاب إلى الشاطئ"],
      ["HIMMA-GEN-SEQ-009", "اللعب بالرمل"],
      ["HIMMA-GEN-SEQ-010", "تنظيف المكان"],
    ] as const;

    for (const [assetId] of generated) {
      const response = await request.get(`/api/media/${assetId}`);
      expect(response.status(), assetId).toBe(200);
      expect(response.headers()["content-type"], assetId).toContain("image/webp");
      expect((await response.body()).byteLength, assetId).toBeGreaterThan(1_000);
    }

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await page.setContent(`
      <main dir="rtl" style="font-family: sans-serif; padding: 24px; background: #F7FBFF; color: #20364D">
        <h1 style="margin:0 0 20px">صور التسلسل المعتمدة — هِمّة</h1>
        <section style="display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:16px">
          ${generated.map(([assetId, label]) => `
            <figure style="margin:0; padding:12px; background:white; border:1px solid #DCE8F2; border-radius:16px">
              <img data-asset="${assetId}" src="/api/media/${assetId}" alt="${label}" style="display:block; width:100%; aspect-ratio:4/3; object-fit:cover; border-radius:12px" />
              <figcaption style="padding-top:8px; text-align:center; font-weight:700">${label}</figcaption>
            </figure>
          `).join("")}
        </section>
      </main>
    `);

    for (const [assetId] of generated) {
      const image = page.locator(`[data-asset="${assetId}"]`);
      await expect(image).toBeVisible();
      await expect.poll(async () => image.evaluate((element) => (element as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
      await expect.poll(async () => image.evaluate((element) => (element as HTMLImageElement).naturalHeight)).toBeGreaterThan(0);
    }

    mkdirSync("playwright-report/screenshots", { recursive: true });
    await page.screenshot({
      path: "playwright-report/screenshots/generated-sequence-assets.png",
      fullPage: true,
    });
  });
});
