import { useState } from "react";
import { apiPost } from "../../services/api";

export default function GapReporter({ storyId }: { storyId?: number }) {
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("");

  async function submit() {
    if (!description.trim()) return;
    const data = await apiPost("/api/v1/gap_reports", { story_id: storyId, description });
    setStatus(`Reported gap ${data.id}`);
    setDescription("");
  }

  return (
    <div className="card-subtle">
      <div className="section-title">
        <h4>Report a Gap</h4>
      </div>
      <textarea
        className="textarea"
        rows={3}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe the missing requirement or inconsistency..."
      />
      <button className="btn btn-primary" onClick={submit}>Submit Gap</button>
      {status && <div className="pill">{status}</div>}
    </div>
  );
}
