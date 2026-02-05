import AccessDenied from "../components/common/AccessDenied";
import Leaderboard from "../components/gamification/Leaderboard";
import { useHasRole } from "../hooks/useRoles";

export default function LeaderboardPage() {
  const allowed = useHasRole(["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>Leaderboard</h1>
      <p>Top contributors across simulation roles and scenarios.</p>
      <Leaderboard />
    </div>
  );
}
