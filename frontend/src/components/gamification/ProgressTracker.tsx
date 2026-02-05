import { useProgress } from "../../hooks/useProgress";

export default function ProgressTracker() {
  const { epics } = useProgress();
  const items = epics.data?.epics || [];
  return (
    <div className="card">
      <div className="section-title">
        <h3>Epic Progress</h3>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((epic: any) => (
          <div key={epic.epic_id} className="card-subtle">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>Epic {epic.epic_id}</strong>
              <span>{epic.completion_percentage}%</span>
            </div>
            <div style={{ height: 8, background: "#e2e8f0", borderRadius: 999, marginTop: 8 }}>
              <div
                style={{
                  height: "100%",
                  width: `${epic.completion_percentage}%`,
                  background: "linear-gradient(90deg, #1d4ed8, #0ea5e9)",
                  borderRadius: 999,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
