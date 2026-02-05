import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../services/api";

interface AchievementItem {
  code: string;
  name: string;
  description?: string;
  points: number;
}

export default function AchievementPanel() {
  const { data } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => apiGet("/api/v1/achievements"),
  });
  const items = (data?.items || []) as AchievementItem[];
  return (
    <div className="card">
      <div className="section-title">
        <h3>Achievements</h3>
        <span className="pill">{items.length}</span>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((ach) => (
          <div key={ach.code} className="card-subtle">
            <strong>{ach.name}</strong>
            <div style={{ color: "#64748b" }}>{ach.description || ach.code}</div>
            <div className="pill">+{ach.points} pts</div>
          </div>
        ))}
      </div>
    </div>
  );
}
