import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SessionResponse } from "../types/api.types";

export type SessionSummary = SessionResponse & { created_at?: string };

type SessionState = {
  sessions: SessionSummary[];
  currentSession?: SessionSummary;
  currentJourneyRunId?: string;
  setCurrentSession: (session: SessionSummary) => void;
  addSession: (session: SessionSummary) => void;
  setCurrentJourneyRunId: (runId: string | undefined) => void;
  clearSessions: () => void;
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSession: undefined,
      currentJourneyRunId: undefined,
      setCurrentSession: (session) => set({ currentSession: session }),
      addSession: (session) => {
        const existing = get().sessions.filter((s) => s.id !== session.id);
        set({ sessions: [session, ...existing].slice(0, 20) });
      },
      setCurrentJourneyRunId: (runId) => set({ currentJourneyRunId: runId }),
      clearSessions: () => set({ sessions: [], currentSession: undefined, currentJourneyRunId: undefined }),
    }),
    { name: "dpp-sessions" },
  ),
);
