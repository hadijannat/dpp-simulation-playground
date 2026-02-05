import { useEffect, useState } from "react";
import { useRoleStore } from "../stores/roleStore";
import { useStories, useSession } from "../hooks/useSimulation";
import SimulationCanvas from "../components/simulation/SimulationCanvas";
import StoryNavigator from "../components/simulation/StoryNavigator";
import StepExecutor from "../components/simulation/StepExecutor";
import ValidationFeedback from "../components/simulation/ValidationFeedback";
import RoleOnboarding from "../components/role-play/RoleOnboarding";
import PerspectiveComparison from "../components/role-play/PerspectiveComparison";
import AnnotationLayer from "../components/collaboration/AnnotationLayer";
import GapReporter from "../components/collaboration/GapReporter";

interface StoryStep {
  action: string;
  params?: Record<string, unknown>;
}

interface Story {
  code: string;
  title: string;
  steps: StoryStep[];
}

export default function SimulationPage() {
  const { role } = useRoleStore();
  const { data } = useStories();
  const { createSession, startStory, executeStep, validateStory } = useSession();
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedCode, setSelectedCode] = useState("");
  const [story, setStory] = useState<Story | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [result, setResult] = useState<unknown>(null);
  const [validation, setValidation] = useState<unknown>(null);

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
      <div className="grid-2">
        <div className="card">
          <div className="section-title">
            <h2>Simulation</h2>
            <span className="pill">Role: {role}</span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-primary" onClick={handleCreateSession}>Create Session</button>
            <input
              className="input"
              placeholder="Session ID"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
            />
          </div>
          <div style={{ marginTop: 12 }}>
            <RoleOnboarding role={role} />
          </div>
          <div style={{ marginTop: 12 }}>
            <PerspectiveComparison left={role} right={role === "regulator" ? "manufacturer" : "regulator"} />
          </div>
        </div>
        <StoryNavigator stories={stories} selectedCode={selectedCode} onSelect={(code) => {
          setSelectedCode(code);
          handleStartStory(code);
        }} />
      </div>

      {story && (
        <>
          <div className="card">
            <h3>{story.title}</h3>
            <SimulationCanvas steps={story.steps} completed={completedSteps} />
          </div>
          <div className="grid-2">
            <StepExecutor storyCode={story.code} steps={story.steps} onExecute={handleExecute} />
            <div style={{ display: "grid", gap: 16 }}>
              <div className="card">
                <div className="section-title">
                  <h3>Run Validation</h3>
                  <button className="btn btn-secondary" onClick={handleValidate}>Validate</button>
                </div>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </div>
              <ValidationFeedback result={validation} />
            </div>
          </div>
          <div className="grid-2">
            <AnnotationLayer />
            <GapReporter />
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
