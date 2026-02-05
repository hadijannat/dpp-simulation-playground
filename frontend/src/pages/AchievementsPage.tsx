import AccessDenied from "../components/common/AccessDenied";
import { useHasRole } from "../hooks/useRoles";

export default function AchievementsPage() {
  const allowed = useHasRole(["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>Achievements</h1>
      <p>Content for achievements.</p>
    </div>
  );
}
