import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import { useJourneyCompliance, useJourneyRun, useDigitalTwin, useCsatFeedback } from "../hooks/useJourney";
import { createNegotiation, createTransfer, runNegotiationAction, runTransferAction } from "../services/platformV2Service";
import { useRoleStore } from "../stores/roleStore";
import { useSessionStore } from "../stores/sessionStore";

type DraftState = {
  past: string[];
  present: string;
};

const DEFAULT_DPP = {
  aas_identifier: "urn:example:manufacturer:001",
  product_name: "FutureCell Pack",
  product_identifier: "FC-2026-001",
};

export default function JourneyPage() {
  const { t, i18n } = useTranslation(["simulation", "common"]);
  const { role } = useRoleStore();
  const currentJourneyRunId = useSessionStore((state) => state.currentJourneyRunId);
  const setCurrentJourneyRunId = useSessionStore((state) => state.setCurrentJourneyRunId);

  const [runId, setRunId] = useState<string | undefined>(currentJourneyRunId);
  const [dppDraft, setDppDraft] = useState<DraftState>({
    past: [],
    present: JSON.stringify(DEFAULT_DPP, null, 2),
  });
  const [complianceRunId, setComplianceRunId] = useState<string | undefined>();
  const [csatScore, setCsatScore] = useState(5);
  const [csatComment, setCsatComment] = useState("");
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const { run, createRun, executeStep } = useJourneyRun(runId);
  const { complianceRun, runCheck, applyFix } = useJourneyCompliance(complianceRunId);
  const csat = useCsatFeedback();

  const parsedDpp = useMemo(() => {
    try {
      return JSON.parse(dppDraft.present) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [dppDraft.present]);

  const twin = useDigitalTwin(
    parsedDpp && typeof parsedDpp.aas_identifier === "string"
      ? parsedDpp.aas_identifier
      : undefined,
  );

  const negotiation = useMutation({
    mutationFn: () =>
      createNegotiation({
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        policy: {
          permission: [{ constraint: { leftOperand: "purpose", rightOperand: "dpp:simulation" } }],
        },
      }),
  });

  const transfer = useMutation({
    mutationFn: () =>
      createTransfer({
        asset_id: "asset-001",
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
      }),
  });

  async function startRun() {
    const created = await createRun.mutateAsync({
      template_code: "manufacturer-core-e2e",
      role,
      locale: i18n.language,
      metadata: { source: "journey-page" },
    });
    setRunId(created.id);
    setCurrentJourneyRunId(created.id);
  }

  async function execute(stepId: string, payload: Record<string, unknown>) {
    if (!runId) return;
    await executeStep.mutateAsync({
      runId,
      stepId,
      body: { payload, metadata: { role } },
    });
    await run.refetch();
  }

  function updateDpp(next: string) {
    setDppDraft((current) => ({ past: [...current.past, current.present], present: next }));
  }

  function undoDpp() {
    setDppDraft((current) => {
      if (current.past.length === 0) return current;
      const previous = current.past[current.past.length - 1];
      return { past: current.past.slice(0, -1), present: previous };
    });
  }

  async function runComplianceCheck() {
    if (!parsedDpp) return;
    const response = await runCheck.mutateAsync({
      payload: parsedDpp,
      regulations: ["ESPR", "Battery Regulation"],
    });
    setComplianceRunId(response.id);
  }

  async function autoFixFirstViolation() {
    const first = complianceRun.data?.violations?.[0];
    if (!complianceRunId || !first || !first.path) return;
    await applyFix.mutateAsync({ runId: complianceRunId, path: first.path, value: "auto-fixed-value" });
    await complianceRun.refetch();
  }

  async function progressNegotiation() {
    const created = await negotiation.mutateAsync();
    const id = String(created.id || "");
    if (!id) return;
    await runNegotiationAction(id, "request");
    await runNegotiationAction(id, "requested");
    await runNegotiationAction(id, "offer");
    await runNegotiationAction(id, "accept");
  }

  async function progressTransfer() {
    const created = await transfer.mutateAsync();
    const id = String(created.id || "");
    if (!id) return;
    await runTransferAction(id, "provision");
    await runTransferAction(id, "provisioned");
    await runTransferAction(id, "request");
    await runTransferAction(id, "requested");
    await runTransferAction(id, "start");
    await runTransferAction(id, "complete");
  }

  async function submitFeedback() {
    await csat.mutateAsync({
      score: csatScore,
      locale: i18n.language,
      role,
      flow: "manufacturer-core-e2e",
      comment: csatComment || undefined,
    });
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card hero-panel">
        <div className="section-title">
          <h1>Manufacturer Journey</h1>
          <span className="pill">v2 · {role}</span>
        </div>
        <p>
          Guided end-to-end path for DPP creation, compliance validation, EDC handover, and post-flow feedback.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={startRun}>
            {t("createSession")}
          </button>
          {currentJourneyRunId && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setRunId(currentJourneyRunId);
              }}
            >
              {t("resumeSession")}
            </button>
          )}
          <button className="btn btn-secondary" onClick={() => setIsEditorOpen(true)}>
            Open Payload Editor
          </button>
        </div>
        {runId && <div style={{ marginTop: 10, color: "var(--ink-muted)" }}>Journey Run ID: {runId}</div>}
      </div>

      <div className="simulation-workspace">
        <div className="card">
          <h3>Journey Steps</h3>
          <div style={{ display: "grid", gap: 8 }}>
            <button className="btn btn-secondary" onClick={() => parsedDpp && execute("create-dpp", parsedDpp)}>
              1. Create DPP
            </button>
            <button className="btn btn-secondary" onClick={runComplianceCheck}>
              2. Run Compliance
            </button>
            <button className="btn btn-secondary" onClick={progressNegotiation}>
              3. Run EDC Negotiation
            </button>
            <button className="btn btn-secondary" onClick={progressTransfer}>
              4. Run EDC Transfer
            </button>
            <button className="btn btn-secondary" onClick={submitFeedback}>
              5. Submit CSAT
            </button>
          </div>
          <div style={{ marginTop: 12 }}>
            <h4>Session Resume</h4>
            <ul className="onboarding-list">
              <li>Last run ID is persisted in local storage.</li>
              <li>Use Resume button to continue where you left off.</li>
              <li>Draft payload editor supports undo for safe edits.</li>
            </ul>
          </div>
        </div>

        <div className="card workspace-panel-full">
          <div className="section-title">
            <h3>Run State</h3>
            <span className="pill">{run.data?.status || "idle"}</span>
          </div>
          <div className="mono-panel">
            <pre>{JSON.stringify(run.data || { status: "not-started" }, null, 2)}</pre>
          </div>

          <div style={{ marginTop: 14 }}>
            <div className="section-title">
              <h3>Compliance State</h3>
              <button className="btn btn-secondary" onClick={autoFixFirstViolation}>
                Apply First Fix
              </button>
            </div>
            <div className="mono-panel">
              <pre>{JSON.stringify(complianceRun.data || { status: "not-run" }, null, 2)}</pre>
            </div>
          </div>

          <div style={{ marginTop: 14 }}>
            <h3>Digital Twin Preview</h3>
            <div className="mono-panel">
              <pre>{JSON.stringify(twin.data || { status: "awaiting-dpp-id" }, null, 2)}</pre>
            </div>
          </div>

          <div style={{ marginTop: 14 }}>
            <h3>CSAT</h3>
            <div className="grid-2">
              <label>
                <div style={{ marginBottom: 6 }}>Score (1-5)</div>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={5}
                  value={csatScore}
                  onChange={(event) => setCsatScore(Number(event.target.value))}
                />
              </label>
              <label>
                <div style={{ marginBottom: 6 }}>Comment</div>
                <input
                  className="input"
                  value={csatComment}
                  onChange={(event) => setCsatComment(event.target.value)}
                />
              </label>
            </div>
            {csat.data && <div style={{ marginTop: 10 }} className="pill">Submitted at {csat.data.created_at}</div>}
          </div>
        </div>

        <div className="card desktop-only">
          <div className="section-title">
            <h3>Payload Editor</h3>
            <button className="btn btn-secondary" onClick={undoDpp} disabled={dppDraft.past.length === 0}>
              Undo
            </button>
          </div>
          <textarea
            className="textarea"
            rows={22}
            value={dppDraft.present}
            onChange={(event) => updateDpp(event.target.value)}
          />
          {!parsedDpp && <div className="error">Invalid JSON payload</div>}
          <div style={{ marginTop: 10 }} className="pill">
            Inline hint: Include `aas_identifier` and `product_name` for best compliance results.
          </div>
        </div>
      </div>

      {isEditorOpen && (
        <>
          <div className="bottom-sheet-overlay mobile-only" onClick={() => setIsEditorOpen(false)} role="presentation" />
          <div className="bottom-sheet mobile-only">
            <div className="section-title">
              <h3>Payload Editor</h3>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-secondary" onClick={undoDpp} disabled={dppDraft.past.length === 0}>
                  Undo
                </button>
                <button className="btn btn-secondary" onClick={() => setIsEditorOpen(false)}>
                  Close
                </button>
              </div>
            </div>
            <textarea
              className="textarea"
              rows={12}
              value={dppDraft.present}
              onChange={(event) => updateDpp(event.target.value)}
            />
            {!parsedDpp && <div className="error">Invalid JSON payload</div>}
          </div>
        </>
      )}
    </div>
  );
}
