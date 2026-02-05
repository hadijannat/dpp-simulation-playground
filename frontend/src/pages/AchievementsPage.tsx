import AccessDenied from "../components/common/AccessDenied";
import AchievementPanel from "../components/gamification/AchievementPanel";
import StreakIndicator from "../components/gamification/StreakIndicator";
import { useHasRole } from "../hooks/useRoles";

export default function AchievementsPage() {
  const allowed = useHasRole(["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>Achievements</h1>
      <p>Track badges and streaks earned through simulation progress.</p>
      <div className="grid-2">
        <AchievementPanel />
        <StreakIndicator />
      </div>
    </div>
  );
}
