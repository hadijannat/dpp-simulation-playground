import { useState } from "react";
import { apiRequest } from "../../services/api";
import MonacoWrapper from "./MonacoWrapper";

export default function RequestBuilder() {
  const [path, setPath] = useState("/api/v1/health");
  const [method, setMethod] = useState("GET");
  const [headers, setHeaders] = useState('{\n  "Content-Type": "application/json"\n}');
  const [body, setBody] = useState("{}");
  const [response, setResponse] = useState<string>("");

  async function run() {
    let parsedHeaders: Record<string, string> = {};
    let parsedBody: any = undefined;
    try {
      parsedHeaders = JSON.parse(headers);
    } catch {
      setResponse("Invalid headers JSON");
      return;
    }
    if (method !== "GET") {
      try {
        parsedBody = JSON.parse(body);
      } catch {
        setResponse("Invalid body JSON");
        return;
      }
    }
    const data = await apiRequest(path, {
      method,
      headers: parsedHeaders,
      body: method === "GET" ? undefined : JSON.stringify(parsedBody),
    });
    setResponse(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <select value={method} onChange={(e) => setMethod(e.target.value)} className="input" style={{ maxWidth: 120 }}>
          <option>GET</option>
          <option>POST</option>
          <option>PATCH</option>
          <option>DELETE</option>
        </select>
        <input value={path} onChange={(e) => setPath(e.target.value)} className="input" />
        <button className="btn btn-primary" onClick={run}>Send</button>
      </div>
      <div className="grid-2">
        <div className="card-subtle">
          <h4>Headers</h4>
          <MonacoWrapper value={headers} onChange={setHeaders} height={160} />
        </div>
        <div className="card-subtle">
          <h4>Body</h4>
          <MonacoWrapper value={body} onChange={setBody} height={160} />
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h4>Response</h4>
        <pre style={{ background: "#0b1a2a", color: "#e2e8f0", padding: 12, borderRadius: 8 }}>
          {response}
        </pre>
      </div>
    </div>
  );
}
