import { expect, test } from "@playwright/test";

test.describe("Journey Integration @integration", () => {
  test("manufacturer journey completes end-to-end against real backend", async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto("/journey");
    await expect(page.getByRole("heading", { name: "Manufacturer Journey" })).toBeVisible();

    await page.getByRole("button", { name: "Start Journey" }).click();
    await expect(page.locator("text=/run-/i")).toBeVisible({ timeout: 15_000 });

    const runIdText = await page.locator("text=/run-/i").first().textContent();
    expect(runIdText).toBeTruthy();

    await page.getByRole("button", { name: "1. Create DPP" }).click();
    await expect(page.locator(".mono-panel").first()).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "2. Run Compliance" }).click();
    await expect(page.locator(".mono-panel").nth(1)).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: "3. Run EDC Negotiation" }).click();
    await expect(page.locator(".mono-panel")).toHaveCount(3, { timeout: 15_000 });

    await page.getByRole("button", { name: "4. Run EDC Transfer" }).click();
    await expect(page.locator(".mono-panel")).toHaveCount(4, { timeout: 15_000 });

    const runStatePanel = page.locator("[data-testid='run-state-panel']");
    if (await runStatePanel.isVisible()) {
      await expect(runStatePanel).toContainText("step", { timeout: 5_000 });
    }

    await page.getByRole("button", { name: "5. Submit CSAT" }).click();
    await expect(page.getByText("Submitted at")).toBeVisible({ timeout: 10_000 });

    expect(consoleErrors).toEqual([]);
  });
});
