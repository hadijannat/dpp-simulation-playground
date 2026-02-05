import { useMutation, useQuery } from "@tanstack/react-query";
import {
  createSession as createSessionRequest,
  executeStep as executeStepRequest,
  listStories,
  startStory as startStoryRequest,
  validateStory as validateStoryRequest,
} from "../services/simulationService";
import { useSessionStore } from "../stores/sessionStore";

export function useStories() {
  return useQuery({
    queryKey: ["stories"],
    queryFn: () => listStories(),
  });
}

export function useSession() {
  const addSession = useSessionStore((state) => state.addSession);
  const setCurrentSession = useSessionStore((state) => state.setCurrentSession);

  const createSession = useMutation({
    mutationFn: (payload: { role: string; state?: Record<string, unknown> }) =>
      createSessionRequest(payload),
    onSuccess: (data) => {
      const session = { ...data, created_at: new Date().toISOString() };
      addSession(session);
      setCurrentSession(session);
    },
  });

  const startStory = useMutation({
    mutationFn: (payload: { sessionId: string; code: string }) =>
      startStoryRequest(payload.sessionId, payload.code),
  });

  const executeStep = useMutation({
    mutationFn: (payload: { sessionId: string; code: string; idx: number; body: Record<string, unknown> }) =>
      executeStepRequest(payload.sessionId, payload.code, payload.idx, payload.body),
  });

  const validateStory = useMutation({
    mutationFn: (payload: { sessionId: string; code: string; body: Record<string, unknown> }) =>
      validateStoryRequest(payload.sessionId, payload.code, payload.body),
  });

  return { createSession, startStory, executeStep, validateStory };
}
