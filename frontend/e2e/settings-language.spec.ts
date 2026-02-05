import { expect, test } from "@playwright/test";

test.describe("Settings Language Switching", () => {
  test("language selection persists across page reload", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();

    await page.getByRole("combobox", { name: /language/i }).selectOption("de");
    await expect(page.getByText(/Einstellungen|Sprache/)).toBeVisible({ timeout: 5_000 });

    await page.reload();
    await expect(page.getByText(/Einstellungen|Sprache/)).toBeVisible({ timeout: 5_000 });

    await page.getByRole("combobox", { name: /language|sprache/i }).selectOption("fr");
    await expect(page.getByText(/Paramètres|Langue/)).toBeVisible({ timeout: 5_000 });

    await page.getByRole("combobox", { name: /language|langue/i }).selectOption("en");
    await expect(page.getByText(/Settings|Language/)).toBeVisible({ timeout: 5_000 });
  });
});
