import { useGamification } from "../hooks/useGamification";
import { useGamificationStore } from "../stores/gamificationStore";
import type { Achievement } from "../types/api.types";

export default function GamificationPage() {
  const { achievements, leaderboard } = useGamification();
  const storedLeaderboard = useGamificationStore((state) => state.leaderboard);
  const leaderboardItems = leaderboard.data?.items ?? storedLeaderboard;

  return (
    <div className="page">
      <h2>Gamification Overview</h2>
      <div className="grid" style={{ display: "grid", gap: 16 }}>
        <div className="card">
          <h3>Achievements Catalog</h3>
          {achievements.isLoading && <div>Loading achievements...</div>}
          {achievements.error && <div className="error">Failed to load achievements.</div>}
          {achievements.data?.items?.length ? (
            <ul>
              {achievements.data.items
                .slice(0, 6)
                .map((item: Achievement, idx: number) => (
                  <li key={`${item.code ?? idx}`}>{item.name ?? item.code}</li>
                ))}
            </ul>
          ) : (
            !achievements.isLoading && <div>No achievements available.</div>
          )}
        </div>

        <div className="card">
          <h3>Leaderboard</h3>
          {leaderboard.isLoading && <div>Loading leaderboard...</div>}
          {leaderboard.error && <div className="error">Failed to load leaderboard.</div>}
          {leaderboardItems.length ? (
            <table className="table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Points</th>
                  <th>Level</th>
                </tr>
              </thead>
              <tbody>
                {leaderboardItems.map((entry) => (
                  <tr key={entry.user_id}>
                    <td>{entry.user_id}</td>
                    <td>{entry.total_points}</td>
                    <td>{entry.level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            !leaderboard.isLoading && <div>No leaderboard data yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
