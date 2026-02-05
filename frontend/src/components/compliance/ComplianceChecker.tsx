import { useState } from "react";
import { apiPost } from "../../services/api";

export default function ComplianceChecker() {
  const [result, setResult] = useState<string>("");
  const [payload, setPayload] = useState("{\n  \"aas_identifier\": \"urn:example:aas:battery-ev-001\"\n}");

  async function run() {
    const data = await apiPost("/api/v1/compliance/check", {
      data: JSON.parse(payload),
      regulations: ["ESPR"],
    });
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
