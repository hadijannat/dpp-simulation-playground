import { useState } from "react";
import { useCompliance } from "../../hooks/useCompliance";

export default function ComplianceChecker() {
  const [result, setResult] = useState<string>("");
  const [payload, setPayload] = useState("{\n  \"aas_identifier\": \"urn:example:aas:battery-ev-001\"\n}");
  const [sessionId, setSessionId] = useState("");
  const [storyCode, setStoryCode] = useState("");
  const { checkCompliance } = useCompliance();

  async function run() {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(payload);
    } catch {
      setResult("Invalid JSON payload");
      return;
    }
    const data = await checkCompliance.mutateAsync({
      data: parsed,
      regulations: ["ESPR", "Battery Regulation", "WEEE", "RoHS"],
      session_id: sessionId || undefined,
      story_code: storyCode || undefined,
    });
    setResult(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input
          className="input"
          placeholder="Session ID (optional)"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{ flex: 1 }}
        />
        <input
          className="input"
          placeholder="Story Code (optional)"
          value={storyCode}
          onChange={(e) => setStoryCode(e.target.value)}
          style={{ flex: 1 }}
        />
      </div>
      <textarea className="textarea" value={payload} onChange={(e) => setPayload(e.target.value)} rows={6} />
      <button className="btn btn-primary" onClick={run}>Run Compliance Check</button>
      <div className="card" style={{ marginTop: 12 }}>
        <pre className="mono-panel">{result}</pre>
      </div>
    </div>
  );
}
