import { useState } from "react";

interface StoryStep {
  action: string;
  params?: Record<string, unknown>;
}

export default function StepExecutor({
  storyCode,
  steps,
  onExecute,
}: {
  storyCode: string;
  steps: StoryStep[];
  onExecute: (idx: number, payload: Record<string, unknown>) => void;
}) {
  const [payload, setPayload] = useState<string>("{}\n");

  function parsedPayload() {
    try {
      return JSON.parse(payload);
    } catch {
      return null;
    }
  }

  return (
    <div className="card">
      <div className="section-title">
        <h3>Step Executor</h3>
        <span className="pill">{storyCode}</span>
      </div>
      <textarea
        className="textarea"
        rows={6}
        value={payload}
        onChange={(e) => setPayload(e.target.value)}
      />
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {steps.map((step, idx) => (
          <div key={`${step.action}-${idx}`} className="card-subtle">
            <div style={{ fontWeight: 600 }}>{idx + 1}. {step.action}</div>
            {step.params && <pre>{JSON.stringify(step.params, null, 2)}</pre>}
            <button
              className="btn btn-primary"
              onClick={() => {
                const parsed = parsedPayload();
                if (!parsed) return;
                onExecute(idx, parsed);
              }}
            >
              Execute Step
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
