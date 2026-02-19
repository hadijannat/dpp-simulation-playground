import { apiGet } from "./api";
import type { Achievement, LeaderboardResponse, LeaderboardWindow, StreakResponse } from "../types/api.types";

export function listAchievements() {
  return apiGet<{ items: Achievement[] }>("/api/v2/gamification/achievements");
}

export function getLeaderboard(options: {
  limit?: number;
  offset?: number;
  window?: LeaderboardWindow;
  role?: string;
} = {}) {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 10),
    offset: String(options.offset ?? 0),
    window: options.window ?? "all",
  });
  if (options.role) params.set("role", options.role);
  return apiGet<LeaderboardResponse>(`/api/v2/gamification/leaderboard?${params.toString()}`);
}

export function getStreaks() {
  return apiGet<StreakResponse>("/api/v2/gamification/streaks");
}
