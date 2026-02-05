import { apiGet } from "./api";
import type { Achievement, LeaderboardResponse } from "../types/api.types";

export function listAchievements() {
  return apiGet<{ items: Achievement[] }>("/api/v2/gamification/achievements");
}

export function getLeaderboard(limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiGet<LeaderboardResponse>(`/api/v2/gamification/leaderboard?${params.toString()}`);
}
