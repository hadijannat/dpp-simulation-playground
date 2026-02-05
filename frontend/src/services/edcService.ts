import { apiGet, apiPost } from "./api";
import type {
  CatalogResponse,
  EDCAssetList,
  EDCParticipantList,
  EDCNegotiation,
  EDCTransfer,
} from "../types/api.types";

export type NegotiationCreatePayload = {
  consumer_id: string;
  provider_id: string;
  asset_id: string;
  policy: Record<string, unknown>;
  session_id?: string;
  purpose?: string;
};

export type TransferCreatePayload = {
  asset_id: string;
  session_id?: string;
  consumer_id?: string;
  provider_id?: string;
};

export function getCatalog() {
  return apiGet<CatalogResponse>("/api/v2/edc/catalog");
}

export function getParticipants() {
  return apiGet<EDCParticipantList>("/api/v2/edc/participants");
}

export function getAssets() {
  return apiGet<EDCAssetList>("/api/v2/edc/assets");
}

export function createNegotiation(payload: NegotiationCreatePayload) {
  return apiPost<EDCNegotiation>("/api/v2/edc/negotiations", payload);
}

export function advanceNegotiation(id: string, action: string, payload?: Record<string, unknown>) {
  return apiPost<EDCNegotiation>(`/api/v2/edc/negotiations/${id}/actions/${action}`, payload ?? {});
}

export function createTransfer(payload: TransferCreatePayload) {
  return apiPost<EDCTransfer>("/api/v2/edc/transfers", payload);
}

export function advanceTransfer(id: string, action: string, payload?: Record<string, unknown>) {
  return apiPost<EDCTransfer>(`/api/v2/edc/transfers/${id}/actions/${action}`, payload ?? {});
}
