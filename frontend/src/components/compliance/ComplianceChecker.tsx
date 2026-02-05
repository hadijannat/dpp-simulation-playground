import { useState } from "react";
import { apiPost } from "../../services/api";

export default function ComplianceChecker() {
  const [result, setResult] = useState<string>("");
  const [payload, setPayload] = useState("{\n  \"aas_identifier\": \"urn:example:aas:battery-ev-001\"\n}");
  const [sessionId, setSessionId] = useState("");
  const [storyCode, setStoryCode] = useState("");

  async function run() {
    const data = await apiPost("/api/v1/compliance/check", {
      data: JSON.parse(payload),
      regulations: ["ESPR"],
      session_id: sessionId || undefined,
      story_code: storyCode || undefined,
    });
    setResult(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input
          placeholder="Session ID (optional)"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{ flex: 1 }}
        />
        <input
          placeholder="Story Code (optional)"
          value={storyCode}
          onChange={(e) => setStoryCode(e.target.value)}
          style={{ flex: 1 }}
        />
      </div>
      <textarea value={payload} onChange={(e) => setPayload(e.target.value)} rows={6} style={{ width: "100%" }} />
      <button onClick={run}>Run Compliance Check</button>
      <pre>{result}</pre>
    </div>
  );
}
