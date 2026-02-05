import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
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
  });

  useEffect(() => {
    if (leaderboard.data?.items) {
      setLeaderboard(leaderboard.data.items);
    }
  }, [leaderboard.data, setLeaderboard]);

  return { achievements, leaderboard };
}
