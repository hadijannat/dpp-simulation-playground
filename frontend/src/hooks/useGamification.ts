import { useQuery } from "@tanstack/react-query";
import { getLeaderboard, listAchievements } from "../services/gamificationService";
import { useGamificationStore } from "../stores/gamificationStore";

export function useGamification() {
  const setLeaderboard = useGamificationStore((state) => state.setLeaderboard);

  const achievements = useQuery({
    queryKey: ["achievements"],
    queryFn: () => listAchievements(),
  });

  const leaderboard = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => getLeaderboard(),
    onSuccess: (data) => {
      if (data?.items) {
        setLeaderboard(data.items);
      }
    },
  });

  return { achievements, leaderboard };
}
