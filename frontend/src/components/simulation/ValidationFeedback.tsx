type ValidationPayload = {
  result?: { status?: string };
  status?: string;
  [key: string]: unknown;
};

export default function ValidationFeedback({ result }: { result: unknown }) {
  if (!result) return null;
  const payload = result as ValidationPayload;
  const status = payload.result?.status || payload.status;
  const badgeClass =
    status === "compliant" || status === "ok" ? "status-ok" : status === "non-compliant" ? "status-bad" : "status-warn";
  return (
    <div className="card">
      <div className="section-title">
        <h3>Validation Feedback</h3>
        <span className={`pill ${badgeClass}`}>{status || "unknown"}</span>
      </div>
      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
