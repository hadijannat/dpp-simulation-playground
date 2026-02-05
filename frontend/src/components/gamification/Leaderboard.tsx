import { useQuery } from "@tanstack/react-query";
import { getLeaderboard } from "../../services/gamificationService";

interface LeaderboardEntry {
  user_id: string;
  total_points: number;
}

export default function Leaderboard() {
  const { data } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => getLeaderboard(),
  });
  const items = (data?.items || []) as LeaderboardEntry[];
  return (
    <div className="card">
      <div className="section-title">
        <h3>Leaderboard</h3>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {items.map((item, idx) => (
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
