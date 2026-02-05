import { apiGet, apiPost } from "./api";
import type { ComplianceResult, ComplianceReportList } from "../types/api.types";

export function checkCompliance(payload: Record<string, unknown>) {
  return apiPost<ComplianceResult>("/api/v1/compliance/check", payload);
}

export function listReports(params?: { session_id?: string; story_code?: string; status?: string; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.session_id) search.set("session_id", params.session_id);
  if (params?.story_code) search.set("story_code", params.story_code);
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiGet<ComplianceReportList>(`/api/v1/reports${query ? `?${query}` : ""}`);
}
