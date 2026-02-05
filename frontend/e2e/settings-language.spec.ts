import { expect, test } from "@playwright/test";

test.describe("Settings Language Switching", () => {
  test("language selection persists across page reload", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();

    const main = page.locator("main");
    await main.getByRole("combobox").selectOption("de");
    await expect(page.getByText(/Einstellungen|Sprache/)).toBeVisible({ timeout: 5_000 });

    await page.reload();
    await expect(page.getByText(/Einstellungen|Sprache/)).toBeVisible({ timeout: 5_000 });

    await page.locator("main").getByRole("combobox").selectOption("fr");
    await expect(page.getByText(/Paramètres|Langue/)).toBeVisible({ timeout: 5_000 });

    await page.locator("main").getByRole("combobox").selectOption("en");
    await expect(page.getByText(/Settings|Language/)).toBeVisible({ timeout: 5_000 });
  });
});
