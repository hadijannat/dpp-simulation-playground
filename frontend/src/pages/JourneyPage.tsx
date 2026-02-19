import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import {
  useJourneyCompliance,
  useJourneyRun,
  useDigitalTwin,
  useDigitalTwinDiff,
  useDigitalTwinHistory,
  useCsatFeedback,
} from "../hooks/useJourney";
import { useJourneyTemplate } from "../hooks/useJourneyTemplate";
import { createNegotiation, createTransfer, runNegotiationAction, runTransferAction } from "../services/platformV2Service";
import { useRoleStore } from "../stores/roleStore";
import { useSessionStore } from "../stores/sessionStore";
import DigitalTwinExplorer from "../components/simulation/DigitalTwinExplorer";
import type { JourneyStepDefinition } from "../types/v2.types";

type DraftState = {
  past: string[];
  present: string;
};

const TEMPLATE_CODE = "manufacturer-core-e2e";

export default function JourneyPage() {
  const { t, i18n } = useTranslation(["journey", "simulation", "common"]);
  const { role } = useRoleStore();
  const currentJourneyRunId = useSessionStore((state) => state.currentJourneyRunId);
  const setCurrentJourneyRunId = useSessionStore((state) => state.setCurrentJourneyRunId);

  const template = useJourneyTemplate(TEMPLATE_CODE);
  const steps: JourneyStepDefinition[] = template.data?.steps || [];

  const defaultPayload = useMemo(() => {
    const createStep = steps.find((s) => s.action === "aas.create");
    return createStep?.default_payload || {};
  }, [steps]);

  const [runId, setRunId] = useState<string | undefined>(currentJourneyRunId);
  const [dppDraft, setDppDraft] = useState<DraftState>({
    past: [],
    present: JSON.stringify(defaultPayload, null, 2),
  });
  const [complianceRunId, setComplianceRunId] = useState<string | undefined>();
  const [csatScore, setCsatScore] = useState(5);
  const [csatComment, setCsatComment] = useState("");
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [fromSnapshotIndex, setFromSnapshotIndex] = useState(0);
  const [toSnapshotIndex, setToSnapshotIndex] = useState(0);

  // Re-init draft when template loads
  useMemo(() => {
    if (Object.keys(defaultPayload).length > 0 && dppDraft.present === "{}") {
      setDppDraft({ past: [], present: JSON.stringify(defaultPayload, null, 2) });
    }
  }, [defaultPayload]);

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

  const dppId = useMemo(
    () => (parsedDpp && typeof parsedDpp.aas_identifier === "string" ? parsedDpp.aas_identifier : undefined),
    [parsedDpp],
  );

  const twin = useDigitalTwin(dppId);
  const twinHistory = useDigitalTwinHistory(dppId, 50, 0);
  const historyItems = twinHistory.data?.items || [];

  useEffect(() => {
    if (historyItems.length === 0) {
      setFromSnapshotIndex(0);
      setToSnapshotIndex(0);
      return;
    }
    const latestIndex = historyItems.length - 1;
    setToSnapshotIndex(latestIndex);
    setFromSnapshotIndex(Math.max(0, latestIndex - 1));
  }, [dppId, historyItems.length]);

  const safeFromSnapshotIndex = Math.max(0, Math.min(fromSnapshotIndex, Math.max(historyItems.length - 1, 0)));
  const safeToSnapshotIndex = Math.max(
    safeFromSnapshotIndex,
    Math.min(toSnapshotIndex, Math.max(historyItems.length - 1, 0)),
  );

  const fromSnapshotId = historyItems[safeFromSnapshotIndex]?.snapshot_id;
  const toSnapshotId = historyItems[safeToSnapshotIndex]?.snapshot_id;

  const twinDiff = useDigitalTwinDiff(dppId, fromSnapshotId, toSnapshotId);

  const negotiation = useMutation({
    mutationFn: () => {
      const negStep = steps.find((s) => s.action === "edc.negotiate");
      const defaults = negStep?.default_payload || {};
      return createNegotiation({
        asset_id: (defaults.asset_id as string) || "asset-001",
        consumer_id: (defaults.consumer_id as string) || "BPNL000000000001",
        provider_id: (defaults.provider_id as string) || "BPNL000000000002",
        policy: {
          permission: [{ constraint: { leftOperand: "purpose", rightOperand: "dpp:simulation" } }],
        },
      });
    },
  });

  const transfer = useMutation({
    mutationFn: () => {
      const txStep = steps.find((s) => s.action === "edc.transfer");
      const defaults = txStep?.default_payload || {};
      return createTransfer({
        asset_id: (defaults.asset_id as string) || "asset-001",
        consumer_id: (defaults.consumer_id as string) || "BPNL000000000001",
        provider_id: (defaults.provider_id as string) || "BPNL000000000002",
      });
    },
  });

  async function startRun() {
    const created = await createRun.mutateAsync({
      template_code: TEMPLATE_CODE,
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
    const complianceStep = steps.find((s) => s.action === "compliance.check");
    const regulations = (complianceStep?.default_payload?.regulations as string[]) || ["ESPR", "Battery Regulation"];
    const response = await runCheck.mutateAsync({ payload: parsedDpp, regulations });
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
      flow: TEMPLATE_CODE,
      comment: csatComment || undefined,
    });
  }

  const stepActions: Record<string, () => void> = {
    "aas.create": () => parsedDpp && execute("create-dpp", parsedDpp),
    "compliance.check": runComplianceCheck,
    "edc.negotiate": progressNegotiation,
    "edc.transfer": progressTransfer,
  };

  function handleFromSnapshotIndexChange(index: number) {
    setFromSnapshotIndex(index);
    setToSnapshotIndex((current) => Math.max(current, index));
  }

  function handleToSnapshotIndexChange(index: number) {
    setToSnapshotIndex(index);
    setFromSnapshotIndex((current) => Math.min(current, index));
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card hero-panel">
        <div className="section-title">
          <h1>{template.data?.name || t("title")}</h1>
          <span className="pill">{t("rolePill")} · {role}</span>
        </div>
        <p>{template.data?.description || t("subtitle")}</p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={startRun}>
            {t("startJourney")}
          </button>
          {currentJourneyRunId && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setRunId(currentJourneyRunId);
              }}
            >
              {t("continueJourney")}
            </button>
          )}
          <button className="btn btn-secondary" onClick={() => setIsEditorOpen(true)}>
            {t("openPayloadEditor")}
          </button>
        </div>
        {runId && <div style={{ marginTop: 10, color: "var(--ink-muted)" }}>{t("journeyRunId")}: {runId}</div>}
      </div>

      <div className="simulation-workspace">
        <div className="card">
          <h2>{t("journeySteps")}</h2>
          <div style={{ display: "grid", gap: 8 }}>
            {steps.map((step, idx) => (
              <button
                key={step.step_key}
                className="btn btn-secondary"
                onClick={stepActions[step.action] || (() => execute(step.step_key, step.default_payload))}
              >
                {idx + 1}. {step.title}
              </button>
            ))}
            {steps.length === 0 && (
              <>
                <button className="btn btn-secondary" onClick={() => parsedDpp && execute("create-dpp", parsedDpp)}>
                  1. {t("createDpp")}
                </button>
                <button className="btn btn-secondary" onClick={runComplianceCheck}>
                  2. {t("runCompliance")}
                </button>
                <button className="btn btn-secondary" onClick={progressNegotiation}>
                  3. {t("runNegotiation")}
                </button>
                <button className="btn btn-secondary" onClick={progressTransfer}>
                  4. {t("runTransfer")}
                </button>
              </>
            )}
            <button className="btn btn-secondary" onClick={submitFeedback}>
              {steps.length > 0 ? steps.length + 1 : 5}. {t("submitCsat")}
            </button>
          </div>
          <div style={{ marginTop: 12 }}>
            <h3>{t("sessionResume")}</h3>
            <ul className="onboarding-list">
              <li>{t("sessionResumeHint1")}</li>
              <li>{t("sessionResumeHint2")}</li>
              <li>{t("sessionResumeHint3")}</li>
            </ul>
          </div>
        </div>

        <div className="card workspace-panel-full">
          <div className="section-title">
            <h2>{t("runState")}</h2>
            <span className="pill">{run.data?.status || t("idle")}</span>
          </div>
          <div className="mono-panel">
            <pre>{JSON.stringify(run.data || { status: t("notStarted") }, null, 2)}</pre>
          </div>

          <div style={{ marginTop: 14 }}>
            <div className="section-title">
              <h2>{t("complianceState")}</h2>
              <button className="btn btn-secondary" onClick={autoFixFirstViolation}>
                {t("applyFirstFix")}
              </button>
            </div>
            <div className="mono-panel">
              <pre>{JSON.stringify(complianceRun.data || { status: t("notRun") }, null, 2)}</pre>
            </div>
          </div>

          <div style={{ marginTop: 14 }}>
            <h2>{t("digitalTwinPreview")}</h2>
            <DigitalTwinExplorer
              twin={twin.data}
              history={twinHistory.data}
              diff={twinDiff.data}
              historyLoading={twinHistory.isLoading}
              diffLoading={twinDiff.isLoading}
              fromSnapshotIndex={safeFromSnapshotIndex}
              toSnapshotIndex={safeToSnapshotIndex}
              onFromSnapshotIndexChange={handleFromSnapshotIndexChange}
              onToSnapshotIndexChange={handleToSnapshotIndexChange}
            />
            {!dppId && (
              <div style={{ marginTop: 10 }} className="pill">
                {t("awaitingDppId")}
              </div>
            )}
          </div>

          <div style={{ marginTop: 14 }}>
            <h2>{t("csat")}</h2>
            <div className="grid-2">
              <label>
                <div style={{ marginBottom: 6 }}>{t("score")}</div>
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
                <div style={{ marginBottom: 6 }}>{t("comment")}</div>
                <input
                  className="input"
                  value={csatComment}
                  onChange={(event) => setCsatComment(event.target.value)}
                />
              </label>
            </div>
            {csat.data && <div style={{ marginTop: 10 }} className="pill">{t("submittedAt")} {csat.data.created_at}</div>}
          </div>
        </div>

        <div className="card desktop-only">
          <div className="section-title">
            <h2>{t("payloadEditor")}</h2>
            <button className="btn btn-secondary" onClick={undoDpp} disabled={dppDraft.past.length === 0}>
              {t("undo")}
            </button>
          </div>
          <textarea
            className="textarea"
            rows={22}
            value={dppDraft.present}
            onChange={(event) => updateDpp(event.target.value)}
          />
          {!parsedDpp && <div className="error">{t("invalidJson")}</div>}
          <div style={{ marginTop: 10 }} className="pill">
            {t("payloadHint")}
          </div>
        </div>
      </div>

      {isEditorOpen && (
        <>
          <div className="bottom-sheet-overlay mobile-only" onClick={() => setIsEditorOpen(false)} role="presentation" />
          <div className="bottom-sheet mobile-only">
            <div className="section-title">
              <h2>{t("payloadEditor")}</h2>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-secondary" onClick={undoDpp} disabled={dppDraft.past.length === 0}>
                  {t("undo")}
                </button>
                <button className="btn btn-secondary" onClick={() => setIsEditorOpen(false)}>
                  {t("close")}
                </button>
              </div>
            </div>
            <textarea
              className="textarea"
              rows={12}
              value={dppDraft.present}
              onChange={(event) => updateDpp(event.target.value)}
            />
            {!parsedDpp && <div className="error">{t("invalidJson")}</div>}
          </div>
        </>
      )}
    </div>
  );
}
