import { apiGet, apiPost } from "./api";
import type {
  SessionResponse,
  StepExecuteResponse,
  Story,
  StoryListResponse,
  StoryValidateResponse,
} from "../types/api.types";

export function listStories() {
  return apiGet<StoryListResponse>("/api/v2/simulation/stories");
}

export function createSession(payload: { role: string; state?: Record<string, unknown> }) {
  return apiPost<SessionResponse>("/api/v2/simulation/sessions", payload);
}

export function startStory(sessionId: string, code: string) {
  return apiPost<{ session_id: string; story: Story; status: string }>(
    `/api/v2/simulation/sessions/${sessionId}/stories/${code}/start`,
    {},
  );
}

export function executeStep(sessionId: string, code: string, idx: number, body: Record<string, unknown>) {
  return apiPost<StepExecuteResponse>(
    `/api/v2/simulation/sessions/${sessionId}/stories/${code}/steps/${idx}/execute`,
    body,
  );
}

export function validateStory(sessionId: string, code: string, body: Record<string, unknown>) {
  return apiPost<StoryValidateResponse>(
    `/api/v2/simulation/sessions/${sessionId}/stories/${code}/validate`,
    body,
  );
}
