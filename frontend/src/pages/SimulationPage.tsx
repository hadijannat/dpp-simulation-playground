import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useRoleStore } from "../stores/roleStore";
import { useSessionStore } from "../stores/sessionStore";
import { useStories, useSession } from "../hooks/useSimulation";
import SimulationCanvas from "../components/simulation/SimulationCanvas";
import StoryNavigator from "../components/simulation/StoryNavigator";
import StepExecutor from "../components/simulation/StepExecutor";
import ValidationFeedback from "../components/simulation/ValidationFeedback";
import RoleOnboarding from "../components/role-play/RoleOnboarding";
import PerspectiveComparison from "../components/role-play/PerspectiveComparison";
import AnnotationLayer from "../components/collaboration/AnnotationLayer";
import GapReporter from "../components/collaboration/GapReporter";
import type { Story } from "../types/api.types";

export default function SimulationPage() {
  const { t } = useTranslation("simulation");
  const { role } = useRoleStore();
  const currentSession = useSessionStore((state) => state.currentSession);
  const { data } = useStories();
  const { createSession, startStory, executeStep, validateStory } = useSession();
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedCode, setSelectedCode] = useState("");
  const [story, setStory] = useState<Story | null>(null);
  const [sessionId, setSessionId] = useState(currentSession?.id || "");
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [result, setResult] = useState<unknown>(null);
  const [validation, setValidation] = useState<unknown>(null);
  const [isStepSheetOpen, setIsStepSheetOpen] = useState(false);

  useEffect(() => {
    if (data?.items) {
      const sorted = [...data.items].sort((a, b) => {
        const epicA = a.epic_code || "";
        const epicB = b.epic_code || "";
        if (epicA !== epicB) return epicA.localeCompare(epicB);
        return (a.order_index || 0) - (b.order_index || 0);
      });
      setStories(sorted);
    }
  }, [data]);

  async function handleCreateSession() {
    const response = await createSession.mutateAsync({ role, state: {} });
    setSessionId(response.id);
  }

  async function handleStartStory(code: string) {
    if (!sessionId) return;
    const response = await startStory.mutateAsync({ sessionId, code });
    setStory(response.story);
    setCompletedSteps([]);
    setResult(null);
    setValidation(null);
  }

  async function handleExecute(idx: number, payload: Record<string, unknown>) {
    if (!sessionId || !story) return;
    const response = await executeStep.mutateAsync({
      sessionId,
      code: story.code,
      idx,
      body: { payload, metadata: { role } },
    });
    setResult(response);
    if (!completedSteps.includes(idx)) {
      setCompletedSteps([...completedSteps, idx]);
    }
  }

  async function handleValidate() {
    if (!sessionId || !story) return;
    const resultData = extractResultData(result);
    const response = await validateStory.mutateAsync({
      sessionId,
      code: story.code,
      body: { data: resultData, regulations: ["ESPR"] },
    });
    setValidation(response);
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="card hero-panel">
        <div className="section-title">
          <h1>{t("title")}</h1>
          <span className="pill">Role: {role}</span>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={handleCreateSession}>{t("createSession")}</button>
          {currentSession?.id && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSessionId(currentSession.id);
              }}
            >
              {t("resumeSession")}
            </button>
          )}
          <input
            className="input"
            placeholder="Session ID"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            style={{ maxWidth: 360 }}
          />
          <button className="btn btn-secondary mobile-only" onClick={() => setIsStepSheetOpen(true)}>
            Open Step Editor
          </button>
        </div>
        <div style={{ marginTop: 12 }}>
          <RoleOnboarding role={role} />
        </div>
        <div style={{ marginTop: 12 }}>
          <PerspectiveComparison left={role} right={role === "regulator" ? "manufacturer" : "regulator"} />
        </div>
      </div>

      {story && (
        <>
          <div className="simulation-workspace">
            <div className="card">
              <StoryNavigator
                stories={stories}
                selectedCode={selectedCode}
                onSelect={(code) => {
                  setSelectedCode(code);
                  handleStartStory(code);
                }}
              />
            </div>
            <div className="card workspace-panel-full">
              <h2>{story.title}</h2>
              <SimulationCanvas steps={story.steps} completed={completedSteps} />
              <div style={{ marginTop: 12, display: "grid", gap: 16 }}>
                <div className="card-subtle">
                  <div className="section-title">
                    <h2>{t("runValidation")}</h2>
                    <button className="btn btn-secondary" onClick={handleValidate}>Validate</button>
                  </div>
                  <div className="pill">Inline hint: include required identifiers before validation.</div>
                  <pre className="mono-panel">{JSON.stringify(result, null, 2)}</pre>
                </div>
                <ValidationFeedback result={validation} />
              </div>
              <div className="grid-2" style={{ marginTop: 12 }}>
                <AnnotationLayer />
                <GapReporter />
              </div>
            </div>
            <div className="card desktop-only">
              <StepExecutor storyCode={story.code} steps={story.steps} onExecute={handleExecute} />
            </div>
          </div>
        </>
      )}

      {!story && (
        <div className="card">
          <StoryNavigator
            stories={stories}
            selectedCode={selectedCode}
            onSelect={(code) => {
              setSelectedCode(code);
              handleStartStory(code);
            }}
          />
        </div>
      )}

      {story && isStepSheetOpen && (
        <>
          <div className="bottom-sheet-overlay mobile-only" onClick={() => setIsStepSheetOpen(false)} role="presentation" />
          <div className="bottom-sheet mobile-only">
            <div className="section-title">
              <h2>Step Editor</h2>
              <button className="btn btn-secondary" onClick={() => setIsStepSheetOpen(false)}>Close</button>
            </div>
            <StepExecutor storyCode={story.code} steps={story.steps} onExecute={handleExecute} />
          </div>
        </>
      )}
    </div>
  );
}

function extractResultData(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object") return {};
  const result = (value as { result?: { data?: Record<string, unknown> } }).result;
  if (!result || typeof result !== "object") return {};
  return result.data || {};
}
