import { useState } from "react";
import { API_BASE } from "../../config/endpoints";

export default function RequestBuilder() {
  const [path, setPath] = useState("/api/v1/health");
  const [response, setResponse] = useState<string>("");

  async function run() {
    const res = await fetch(`${API_BASE}${path}`);
    const data = await res.json();
    setResponse(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input value={path} onChange={(e) => setPath(e.target.value)} style={{ flex: 1 }} />
        <button onClick={run}>Send</button>
      </div>
      <pre style={{ background: "#0b1a2a", color: "#e2e8f0", padding: 12 }}>{response}</pre>
    </div>
  );
}
