import { create } from "zustand";
import type { LeaderboardEntry } from "../types/api.types";

type GamificationState = {
  leaderboard: LeaderboardEntry[];
  setLeaderboard: (items: LeaderboardEntry[]) => void;
};

export const useGamificationStore = create<GamificationState>((set) => ({
  leaderboard: [],
  setLeaderboard: (items) => set({ leaderboard: items }),
}));
