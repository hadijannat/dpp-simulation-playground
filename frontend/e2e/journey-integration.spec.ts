import { expect, test } from "@playwright/test";

const API_URL = process.env.VITE_API_URL || "http://127.0.0.1:8106";

test.describe("Journey Integration @integration", () => {
  test.beforeAll(async () => {
    const healthUrl = `${API_URL}/api/v2/health`;
    const response = await fetch(healthUrl, { signal: AbortSignal.timeout(5_000) });

    expect(response.ok, `Expected backend health check to pass at ${healthUrl}`).toBe(true);
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

    const runCreated = page.waitForResponse((response) =>
      response.url().includes("/api/v2/journeys/runs") &&
      response.request().method() === "POST" &&
      response.ok()
    );
    await page.getByRole("button", { name: "Start Journey" }).click();
    const run = await (await runCreated).json() as { id: string };
    await expect(page.getByText(`Journey Run ID: ${run.id}`)).toBeVisible({ timeout: 15_000 });

    const createDpp = page.waitForResponse((response) =>
      response.url().includes(`/api/v2/journeys/runs/${run.id}/steps/create-dpp/execute`) && response.ok()
    );
    await page.getByRole("button", { name: /1\.\s*Create Digital Product Passport/ }).click();
    await createDpp;
    await expect(page.locator(".mono-panel").first()).toContainText('"step_id": "create-dpp"', { timeout: 10_000 });

    const addSubmodel = page.waitForResponse((response) =>
      response.url().includes(`/api/v2/journeys/runs/${run.id}/steps/add-submodel/execute`) && response.ok()
    );
    await page.getByRole("button", { name: /2\.\s*Add Technical Data Submodel/ }).click();
    await addSubmodel;
    await expect(page.locator(".mono-panel").first()).toContainText('"step_id": "add-submodel"', { timeout: 10_000 });

    const complianceRun = page.waitForResponse((response) =>
      response.url().includes("/api/v2/compliance/runs") &&
      response.request().method() === "POST" &&
      response.ok()
    );
    await page.getByRole("button", { name: /3\.\s*Run Compliance Check/ }).click();
    const compliance = await (await complianceRun).json() as { id: string };
    await expect(page.locator(".mono-panel").nth(1)).toContainText(compliance.id, { timeout: 10_000 });

    const negotiationAccepted = page.waitForResponse((response) =>
      response.url().includes("/api/v2/edc/negotiations/") &&
      response.url().includes("/actions/accept") &&
      response.ok()
    );
    await page.getByRole("button", { name: /4\.\s*Negotiate Data Transfer/ }).click();
    await negotiationAccepted;

    const transferCompleted = page.waitForResponse((response) =>
      response.url().includes("/api/v2/edc/transfers/") &&
      response.url().includes("/actions/complete") &&
      response.ok()
    );
    await page.getByRole("button", { name: /5\.\s*Execute Data Transfer/ }).click();
    await transferCompleted;

    const feedbackSubmitted = page.waitForResponse((response) =>
      response.url().includes("/api/v2/feedback/csat") &&
      response.request().method() === "POST" &&
      response.ok()
    );
    await page.getByRole("button", { name: /6\.\s*Submit CSAT/ }).click();
    await feedbackSubmitted;
    await expect(page.getByText(/submitted at/i)).toBeVisible({ timeout: 10_000 });

    const relevant = consoleErrors.filter((e) => !e.includes("favicon"));
    expect(relevant).toEqual([]);
  });
});
