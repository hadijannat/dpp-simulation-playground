export default function ValidationFeedback({ result }: { result: any }) {
  if (!result) return null;
  const status = result?.result?.status || result?.status;
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
