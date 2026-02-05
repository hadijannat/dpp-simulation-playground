import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../services/api";

export default function Leaderboard() {
  const { data } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => apiGet("/api/v1/leaderboard"),
  });
  const items = data?.items || [];
  return (
    <div className="card">
      <div className="section-title">
        <h3>Leaderboard</h3>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((item: any, idx: number) => (
          <div key={item.user_id} className="card-subtle" style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <strong>#{idx + 1}</strong> {item.user_id}
            </div>
            <div>{item.total_points} pts</div>
          </div>
        ))}
      </div>
    </div>
  );
}
