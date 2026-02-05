import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../services/api";
import type { StreakEntry, StreakResponse } from "../../types/api.types";

export default function StreakIndicator() {
  const { data } = useQuery({
    queryKey: ["streaks"],
    queryFn: () => apiGet<StreakResponse>("/api/v2/gamification/streaks"),
  });
  const items: StreakEntry[] = data?.items || [];
  return (
    <div className="card">
      <div className="section-title">
        <h3>Streaks</h3>
        <span className="pill">{items.length}</span>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((item) => (
          <div key={item.user_id} className="card-subtle">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>{item.user_id}</span>
              <strong>{item.current_streak_days} days</strong>
            </div>
            <div style={{ color: "#64748b" }}>Longest: {item.longest_streak_days}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
