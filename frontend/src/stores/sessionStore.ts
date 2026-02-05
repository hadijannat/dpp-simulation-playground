import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SessionResponse } from "../types/api.types";

export type SessionSummary = SessionResponse & { created_at?: string };

type SessionState = {
  sessions: SessionSummary[];
  currentSession?: SessionSummary;
  setCurrentSession: (session: SessionSummary) => void;
  addSession: (session: SessionSummary) => void;
  clearSessions: () => void;
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSession: undefined,
      setCurrentSession: (session) => set({ currentSession: session }),
      addSession: (session) => {
        const existing = get().sessions.filter((s) => s.id !== session.id);
        set({ sessions: [session, ...existing].slice(0, 20) });
      },
      clearSessions: () => set({ sessions: [], currentSession: undefined }),
    }),
    { name: "dpp-sessions" },
  ),
);
