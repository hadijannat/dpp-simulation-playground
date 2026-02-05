import { expect, test } from "@playwright/test";

const API_URL = process.env.VITE_API_URL || "http://127.0.0.1:8106";

test.describe("Journey Integration @integration", () => {
  test.beforeAll(async () => {
    try {
      const response = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5_000) });
      if (!response.ok) test.skip(true, "Backend not reachable");
    } catch {
      test.skip(true, "Backend not reachable");
    }
  });

  test("manufacturer journey completes end-to-end against real backend", async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto("/journey");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: "Start Journey" }).click();
    await expect(page.getByText("Journey Run ID:")).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: /1\.\s*Create DPP/ }).click();
    await expect(page.locator(".mono-panel").first()).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: /2\.\s*Run Compliance/ }).click();
    await expect(page.locator(".mono-panel").nth(1)).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: /3\.\s*Run EDC Negotiation/ }).click();
    await expect(page.locator(".mono-panel")).toHaveCount(3, { timeout: 15_000 });

    await page.getByRole("button", { name: /4\.\s*Run EDC Transfer/ }).click();
    await expect(page.locator(".mono-panel")).toHaveCount(4, { timeout: 15_000 });

    await page.getByRole("button", { name: /5\.\s*Submit CSAT/ }).click();
    await expect(page.getByText(/submitted at/i)).toBeVisible({ timeout: 10_000 });

    const relevant = consoleErrors.filter((e) => !e.includes("favicon"));
    expect(relevant).toEqual([]);
  });
});
