import { useState } from "react";
import { API_BASE } from "../../config/endpoints";

export default function ComplianceChecker() {
  const [result, setResult] = useState<string>("");
  const [payload, setPayload] = useState("{\n  \"aas_identifier\": \"urn:example:aas:battery-ev-001\"\n}");

  async function run() {
    const res = await fetch(`${API_BASE}/api/v1/compliance/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: JSON.parse(payload), regulations: ["ESPR"] }),
    });
    const data = await res.json();
    setResult(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <textarea value={payload} onChange={(e) => setPayload(e.target.value)} rows={6} style={{ width: "100%" }} />
      <button onClick={run}>Run Compliance Check</button>
      <pre>{result}</pre>
    </div>
  );
}
