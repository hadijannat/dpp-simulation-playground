import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const pages = [
  { name: "Home", path: "/" },
  { name: "Journey", path: "/journey" },
  { name: "Simulation", path: "/simulation" },
  { name: "Profile", path: "/profile" },
  { name: "Settings", path: "/settings" },
];

test.describe("Accessibility", () => {
  for (const { name, path } of pages) {
    test(`${name} page (${path}) has no accessibility violations`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page }).analyze();

      if (results.violations.length > 0) {
        const violationSummary = results.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.length,
          helpUrl: v.helpUrl,
        }));
        console.log(
          `Accessibility violations on ${name} (${path}):`,
          JSON.stringify(violationSummary, null, 2)
        );
      }

      expect(results.violations).toHaveLength(0);
    });
  }
});
