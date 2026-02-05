import { apiGet, apiPost } from "./api";
import type { ComplianceRun, CsatFeedback, DigitalTwin, JourneyRun } from "../types/v2.types";
import type { components } from "../types/generated/platform-api";

type Schemas = components["schemas"];

export function createJourneyRun(payload: {
  template_code?: string;
  role: string;
  locale: string;
  metadata?: Record<string, unknown>;
}) {
  return apiPost<JourneyRun>("/api/v2/journeys/runs", payload);
}

export function getJourneyRun(id: string) {
  return apiGet<JourneyRun>(`/api/v2/journeys/runs/${id}`);
}

export function executeJourneyStep(
  runId: string,
  stepId: string,
  payload: { payload: Record<string, unknown>; metadata?: Record<string, unknown> },
) {
  return apiPost<{ run_id: string; execution: JourneyRun["steps"][number]; next_step: string }>(
    `/api/v2/journeys/runs/${runId}/steps/${stepId}/execute`,
    payload,
  );
}

export function runCompliance(payload: {
  dpp_id?: string;
  regulations?: string[];
  payload: Record<string, unknown>;
}) {
  return apiPost<ComplianceRun>("/api/v2/compliance/runs", payload);
}

export function getComplianceRun(runId: string) {
  return apiGet<ComplianceRun>(`/api/v2/compliance/runs/${runId}`);
}

export function applyComplianceFix(runId: string, payload: { path: string; value: unknown }) {
  return apiPost<Schemas["ComplianceFixResponse"]>(
    `/api/v2/compliance/runs/${runId}/apply-fix`,
    payload,
  );
}

export function createNegotiation(payload: {
  asset_id: string;
  consumer_id: string;
  provider_id: string;
  policy: Record<string, unknown>;
}) {
  return apiPost<Schemas["NegotiationResponse"]>("/api/v2/edc/negotiations", payload);
}

export function runNegotiationAction(negotiationId: string, action: string) {
  return apiPost<Schemas["NegotiationResponse"]>(`/api/v2/edc/negotiations/${negotiationId}/actions/${action}`, {});
}

export function createTransfer(payload: Schemas["TransferCreate"]) {
  return apiPost<Schemas["TransferResponse"]>("/api/v2/edc/transfers", payload);
}

export function runTransferAction(transferId: string, action: string) {
  return apiPost<Schemas["TransferResponse"]>(`/api/v2/edc/transfers/${transferId}/actions/${action}`, {});
}

export function getDigitalTwin(dppId: string) {
  return apiGet<DigitalTwin>(`/api/v2/digital-twins/${dppId}`);
}

export function submitCsat(payload: {
  score: number;
  locale: string;
  role: string;
  flow: string;
  comment?: string;
}) {
  return apiPost<CsatFeedback>("/api/v2/feedback/csat", payload);
}
