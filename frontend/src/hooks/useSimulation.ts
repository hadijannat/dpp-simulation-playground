import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "../services/api";

export function useStories() {
  return useQuery({
    queryKey: ["stories"],
    queryFn: () => apiGet("/api/v1/stories"),
  });
}

export function useSession() {
  const createSession = useMutation({
    mutationFn: (payload: { role: string; state?: Record<string, unknown> }) =>
      apiPost("/api/v1/sessions", payload),
  });

  const startStory = useMutation({
    mutationFn: (payload: { sessionId: string; code: string }) =>
      apiPost(`/api/v1/sessions/${payload.sessionId}/stories/${payload.code}/start`, {}),
  });

  const executeStep = useMutation({
    mutationFn: (payload: { sessionId: string; code: string; idx: number; body: Record<string, unknown> }) =>
      apiPost(`/api/v1/sessions/${payload.sessionId}/stories/${payload.code}/steps/${payload.idx}/execute`, payload.body),
  });

  const validateStory = useMutation({
    mutationFn: (payload: { sessionId: string; code: string; body: Record<string, unknown> }) =>
      apiPost(`/api/v1/sessions/${payload.sessionId}/stories/${payload.code}/validate`, payload.body),
  });

  return { createSession, startStory, executeStep, validateStory };
}
