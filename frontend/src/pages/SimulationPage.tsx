import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../services/api";
import { useRoleStore } from "../stores/roleStore";

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
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedCode, setSelectedCode] = useState<string>("");
  const [story, setStory] = useState<Story | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [payload, setPayload] = useState<string>("{}\n");
  const [result, setResult] = useState<string>("");

  useEffect(() => {
    apiGet("/api/v1/stories").then((data) => {
      setStories(data.items || []);
    });
  }, []);

  async function createSession() {
    const data = await apiPost("/api/v1/sessions", { role, state: {} });
    setSessionId(data.id);
  }

  async function startStory() {
    if (!sessionId || !selectedCode) return;
    const data = await apiPost(`/api/v1/sessions/${sessionId}/stories/${selectedCode}/start`, {});
    setStory(data.story);
  }

  async function runStep(idx: number) {
    if (!sessionId || !story) return;
    let parsed: Record<string, unknown> = {};
    try {
        parsed = JSON.parse(payload);
    } catch {
        setResult("Invalid JSON payload");
        return;
    }
    const body = { payload: parsed };
    const data = await apiPost(
      `/api/v1/sessions/${sessionId}/stories/${story.code}/steps/${idx}/execute`,
      body
    );
    setResult(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <h1>Simulation</h1>
      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <button onClick={createSession}>Create Session</button>
        <input
          placeholder="Session ID"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{ flex: 1 }}
        />
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <select value={selectedCode} onChange={(e) => setSelectedCode(e.target.value)}>
          <option value="">Select story</option>
          {stories.map((s) => (
            <option key={s.code} value={s.code}>
              {s.code} - {s.title}
            </option>
          ))}
        </select>
        <button onClick={startStory} disabled={!sessionId || !selectedCode}>
          Start Story
        </button>
      </div>

      {story && (
        <div>
          <h2>{story.title}</h2>
          <textarea
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            rows={6}
            style={{ width: "100%", marginBottom: 8 }}
          />
          <div style={{ display: "grid", gap: 8 }}>
            {story.steps.map((step, idx) => (
              <div key={`${step.action}-${idx}`} style={{ border: "1px solid #e2e8f0", padding: 8 }}>
                <div style={{ fontWeight: 600 }}>{idx + 1}. {step.action}</div>
                {step.params && <pre>{JSON.stringify(step.params, null, 2)}</pre>}
                <button onClick={() => runStep(idx)}>Execute Step</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 16 }}>
          <h3>Result</h3>
          <pre style={{ background: "#0b1a2a", color: "#e2e8f0", padding: 12 }}>{result}</pre>
        </div>
      )}
    </div>
  );
}
