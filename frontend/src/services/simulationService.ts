import { apiGet, apiPost } from "./api";
import type { StoryListResponse, SessionResponse } from "../types/api.types";

export function listStories() {
  return apiGet<StoryListResponse>("/api/v1/stories");
}

export function createSession(payload: { role: string; state?: Record<string, unknown> }) {
  return apiPost<SessionResponse>("/api/v1/sessions", payload);
}

export function startStory(sessionId: string, code: string) {
  return apiPost<{ session_id: string; story: unknown; status: string }>(
    `/api/v1/sessions/${sessionId}/stories/${code}/start`,
    {},
  );
}

export function executeStep(sessionId: string, code: string, idx: number, body: Record<string, unknown>) {
  return apiPost<{ result: unknown }>(
    `/api/v1/sessions/${sessionId}/stories/${code}/steps/${idx}/execute`,
    body,
  );
}

export function validateStory(sessionId: string, code: string, body: Record<string, unknown>) {
  return apiPost<{ session_id: string; story_code: string; result: unknown }>(
    `/api/v1/sessions/${sessionId}/stories/${code}/validate`,
    body,
  );
}
