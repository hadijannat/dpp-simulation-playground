import { useSessionStore } from "../sessionStore";
import type { SessionSummary } from "../sessionStore";

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("sessionStore", () => {
  beforeEach(() => {
    // Reset the store to its initial state before each test
    const { clearSessions } = useSessionStore.getState();
    clearSessions();
  });

  it("has undefined currentSession in initial state", () => {
    const { currentSession } = useSessionStore.getState();
    expect(currentSession).toBeUndefined();
  });

  it("has undefined currentJourneyRunId in initial state", () => {
    const { currentJourneyRunId } = useSessionStore.getState();
    expect(currentJourneyRunId).toBeUndefined();
  });

  it("has empty sessions array in initial state", () => {
    const { sessions } = useSessionStore.getState();
    expect(sessions).toEqual([]);
  });

  it("setCurrentSession updates the currentSession", () => {
    const session: SessionSummary = {
      id: "session-1",
      user_id: "user-1",
      role: "manufacturer",
      state: { step: 1 },
      created_at: "2025-01-01T00:00:00Z",
    };

    useSessionStore.getState().setCurrentSession(session);

    const { currentSession } = useSessionStore.getState();
    expect(currentSession).toEqual(session);
    expect(currentSession?.id).toBe("session-1");
  });

  it("clearSessions resets state to initial values", () => {
    // Set some state first
    const session: SessionSummary = {
      id: "session-2",
      user_id: "user-2",
      role: "developer",
      state: {},
    };
    useSessionStore.getState().setCurrentSession(session);
    useSessionStore.getState().addSession(session);
    useSessionStore.getState().setCurrentJourneyRunId("run-xyz");

    // Verify state was set
    expect(useSessionStore.getState().currentSession).toBeDefined();
    expect(useSessionStore.getState().currentJourneyRunId).toBe("run-xyz");
    expect(useSessionStore.getState().sessions).toHaveLength(1);

    // Clear
    useSessionStore.getState().clearSessions();

    // Verify reset
    const state = useSessionStore.getState();
    expect(state.currentSession).toBeUndefined();
    expect(state.currentJourneyRunId).toBeUndefined();
    expect(state.sessions).toEqual([]);
  });

  it("setCurrentJourneyRunId updates the journeyRunId", () => {
    useSessionStore.getState().setCurrentJourneyRunId("run-123");
    expect(useSessionStore.getState().currentJourneyRunId).toBe("run-123");
  });

  it("setCurrentJourneyRunId can set to undefined", () => {
    useSessionStore.getState().setCurrentJourneyRunId("run-123");
    useSessionStore.getState().setCurrentJourneyRunId(undefined);
    expect(useSessionStore.getState().currentJourneyRunId).toBeUndefined();
  });

  it("addSession adds a session to the list", () => {
    const session: SessionSummary = {
      id: "session-a",
      user_id: "user-a",
      role: "manufacturer",
      state: {},
    };
    useSessionStore.getState().addSession(session);
    expect(useSessionStore.getState().sessions).toHaveLength(1);
    expect(useSessionStore.getState().sessions[0].id).toBe("session-a");
  });

  it("addSession deduplicates by id and prepends newest", () => {
    const session1: SessionSummary = { id: "s1", user_id: "u1", role: "manufacturer", state: {} };
    const session2: SessionSummary = { id: "s2", user_id: "u1", role: "manufacturer", state: {} };
    const session1Updated: SessionSummary = { id: "s1", user_id: "u1", role: "developer", state: { updated: true } };

    useSessionStore.getState().addSession(session1);
    useSessionStore.getState().addSession(session2);
    useSessionStore.getState().addSession(session1Updated);

    const { sessions } = useSessionStore.getState();
    expect(sessions).toHaveLength(2);
    // Updated session1 should be first (newest)
    expect(sessions[0].id).toBe("s1");
    expect(sessions[0].role).toBe("developer");
    expect(sessions[1].id).toBe("s2");
  });

  it("addSession caps at 20 sessions", () => {
    for (let i = 0; i < 25; i++) {
      useSessionStore.getState().addSession({
        id: `session-${i}`,
        user_id: "user",
        role: "manufacturer",
        state: {},
      });
    }
    expect(useSessionStore.getState().sessions).toHaveLength(20);
  });
});
