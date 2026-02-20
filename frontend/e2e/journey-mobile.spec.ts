import { expect, test } from "@playwright/test";

type JourneyStepResult = {
  step_id: string;
  status: string;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  executed_at: string;
};

test("manufacturer mobile journey completes end-to-end flow", async ({ page }) => {
  const consoleErrors: string[] = [];
  const negotiationActions: string[] = [];
  const transferActions: string[] = [];

  let complianceRunId = "cmp-001";
  let feedbackCounter = 0;

  const now = () => new Date().toISOString();

  const journeyRun = {
    id: "run-001",
    template_code: "manufacturer-core-e2e",
    role: "manufacturer",
    locale: "en",
    status: "active",
    current_step: "step-1",
    steps: [] as JourneyStepResult[],
    metadata: { source: "journey-page" },
    created_at: now(),
    updated_at: now(),
  };

  const complianceRun = {
    id: complianceRunId,
    status: "non-compliant",
    dpp_id: "urn:example:manufacturer:001",
    regulations: ["ESPR", "Battery Regulation"],
    payload: {},
    violations: [
      {
        id: "rule-product-name",
        path: "$.product_name",
        message: "product_name is required",
        severity: "high",
      },
    ],
    warnings: [],
    recommendations: [],
    summary: {
      violations: 1,
      warnings: 0,
      recommendations: 0,
    },
    created_at: now(),
    updated_at: now(),
  };

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });

  await page.route("**/api/v2/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });

    let requestBody: Record<string, unknown>;
    try {
      requestBody = request.postDataJSON() as Record<string, unknown>;
    } catch {
      requestBody = {};
    }

    if (method === "POST" && path === "/api/v2/journeys/runs") {
      journeyRun.locale = String(requestBody.locale || "en");
      journeyRun.role = String(requestBody.role || "manufacturer");
      return json(200, journeyRun);
    }

    if (method === "GET" && path === `/api/v2/journeys/runs/${journeyRun.id}`) {
      return json(200, journeyRun);
    }

    if (method === "POST" && path.startsWith(`/api/v2/journeys/runs/${journeyRun.id}/steps/`)) {
      const stepId = path.split("/")[7] || "unknown-step";
      const execution: JourneyStepResult = {
        step_id: stepId,
        status: "completed",
        payload: (requestBody.payload || {}) as Record<string, unknown>,
        metadata: (requestBody.metadata || {}) as Record<string, unknown>,
        executed_at: now(),
      };
      journeyRun.steps.push(execution);
      journeyRun.current_step = `step-${journeyRun.steps.length + 1}`;
      journeyRun.updated_at = execution.executed_at;
      return json(200, {
        run_id: journeyRun.id,
        execution,
        next_step: journeyRun.current_step,
      });
    }

    if (method === "POST" && path === "/api/v2/compliance/runs") {
      complianceRunId = `cmp-${Date.now()}`;
      complianceRun.id = complianceRunId;
      complianceRun.payload = (requestBody.payload || {}) as Record<string, unknown>;
      complianceRun.updated_at = now();
      return json(200, complianceRun);
    }

    if (method === "GET" && path === `/api/v2/compliance/runs/${complianceRunId}`) {
      return json(200, complianceRun);
    }

    if (method === "GET" && path.startsWith("/api/v2/digital-twins/")) {
      const dppId = decodeURIComponent(path.replace("/api/v2/digital-twins/", ""));
      return json(200, {
        dpp_id: dppId,
        nodes: [
          { id: "product", label: "Product", type: "asset" },
          { id: "compliance", label: "Compliance", type: "status" },
          { id: "transfer", label: "Transfer", type: "dataspace" },
        ],
        edges: [
          { id: "product-compliance", source: "product", target: "compliance" },
          { id: "compliance-transfer", source: "compliance", target: "transfer" },
        ],
        timeline: [],
      });
    }

    if (method === "POST" && path === "/api/v2/edc/negotiations") {
      return json(200, {
        id: "neg-001",
        state: "INITIAL",
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        policy: (requestBody.policy || {}) as Record<string, unknown>,
        state_history: [],
      });
    }

    if (method === "POST" && path.startsWith("/api/v2/edc/negotiations/neg-001/actions/")) {
      const action = path.split("/").pop() || "unknown";
      negotiationActions.push(action);
      return json(200, {
        id: "neg-001",
        state: action.toUpperCase(),
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        policy: {},
        state_history: negotiationActions.map((item) => ({ state: item.toUpperCase(), timestamp: now() })),
      });
    }

    if (method === "POST" && path === "/api/v2/edc/transfers") {
      return json(200, {
        id: "trf-001",
        state: "INITIAL",
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        state_history: [],
      });
    }

    if (method === "POST" && path.startsWith("/api/v2/edc/transfers/trf-001/actions/")) {
      const action = path.split("/").pop() || "unknown";
      transferActions.push(action);
      return json(200, {
        id: "trf-001",
        state: action.toUpperCase(),
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        state_history: transferActions.map((item) => ({ state: item.toUpperCase(), timestamp: now() })),
      });
    }

    if (method === "GET" && path.startsWith("/api/v2/journeys/templates")) {
      return json(200, {
        code: "manufacturer-core-e2e",
        name: "Manufacturer Journey",
        description: "End-to-end DPP journey",
        steps: [],
      });
    }

    if (method === "POST" && path === "/api/v2/feedback/csat") {
      feedbackCounter += 1;
      return json(200, {
        id: `feedback-${feedbackCounter}`,
        score: requestBody.score || 5,
        locale: requestBody.locale || "en",
        role: requestBody.role || "manufacturer",
        flow: requestBody.flow || "manufacturer-core-e2e",
        comment: requestBody.comment || null,
        created_at: now(),
      });
    }

    return json(404, { detail: `Unhandled route ${method} ${path}` });
  });

  await page.goto("/journey");
  await expect(page.getByRole("heading", { name: "Manufacturer Journey" })).toBeVisible();

  await page.getByRole("button", { name: "Open Payload Editor" }).click();
  await expect(page.locator(".bottom-sheet")).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await expect(page.locator(".bottom-sheet")).not.toBeVisible();

  await page.getByRole("button", { name: "Start Journey" }).click();
  await expect(page.getByText("Journey Run ID: run-001")).toBeVisible();

  await page.getByRole("button", { name: "1. Create DPP" }).click();
  await expect(page.locator(".mono-panel").first()).toContainText('"step_id": "create-dpp"');

  await page.getByRole("button", { name: "2. Run Compliance" }).click();
  await expect(page.locator(".mono-panel").nth(1)).toContainText("non-compliant");

  await page.getByRole("button", { name: "3. Run EDC Negotiation" }).click();
  await expect.poll(() => negotiationActions.join(",")).toBe("request,requested,offer,accept");

  await page.getByRole("button", { name: "4. Run EDC Transfer" }).click();
  await expect.poll(() => transferActions.join(",")).toBe("provision,provisioned,request,requested,start,complete");

  await page.getByRole("button", { name: "5. Submit CSAT" }).click();
  await expect(page.getByText("Submitted at")).toBeVisible();
  expect(feedbackCounter).toBe(1);

  expect(consoleErrors).toEqual([]);
});
