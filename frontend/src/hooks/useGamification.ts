import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { getLeaderboard, getStreaks, listAchievements } from "../services/gamificationService";
import { useGamificationStore } from "../stores/gamificationStore";
import type { LeaderboardWindow } from "../types/api.types";

interface UseGamificationOptions {
  limit?: number;
  offset?: number;
  window?: LeaderboardWindow;
  role?: string;
}

export function useGamification(options: UseGamificationOptions = {}) {
  const { limit = 10, offset = 0, window = "all", role } = options;
  const setLeaderboard = useGamificationStore((state) => state.setLeaderboard);

  const achievements = useQuery({
    queryKey: ["achievements"],
    queryFn: () => listAchievements(),
    refetchInterval: 20000,
  });

  const leaderboard = useQuery({
    queryKey: ["leaderboard", limit, offset, window, role || "all-roles"],
    queryFn: () => getLeaderboard({ limit, offset, window, role }),
    refetchInterval: 15000,
  });

  const streaks = useQuery({
    queryKey: ["streaks"],
    queryFn: () => getStreaks(),
    refetchInterval: 20000,
  });

  useEffect(() => {
    if (leaderboard.data?.items) {
      setLeaderboard(leaderboard.data.items);
    }
  }, [leaderboard.data, setLeaderboard]);

  return { achievements, leaderboard, streaks };
}
