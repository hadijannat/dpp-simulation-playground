import AccessDenied from "../components/common/AccessDenied";
import { useHasRole } from "../hooks/useRoles";

export default function LeaderboardPage() {
  const allowed = useHasRole(["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>Leaderboard</h1>
      <p>Content for leaderboard.</p>
    </div>
  );
}
