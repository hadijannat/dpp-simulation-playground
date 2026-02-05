import { apiGet, apiPost } from "./api";

export function getCatalog() {
  return apiGet<Record<string, unknown>>("/api/v1/edc/catalog");
}

export function getParticipants() {
  return apiGet<{ items?: unknown[] }>("/api/v1/edc/participants");
}

export function getAssets() {
  return apiGet<{ items?: unknown[] }>("/api/v1/edc/assets");
}

export function createNegotiation(payload: Record<string, unknown>) {
  return apiPost<Record<string, unknown>>("/api/v1/edc/negotiations", payload);
}

export function advanceNegotiation(id: string, action: string, payload?: Record<string, unknown>) {
  return apiPost<Record<string, unknown>>(`/api/v1/edc/negotiations/${id}/${action}`, payload ?? {});
}

export function createTransfer(payload: Record<string, unknown>) {
  return apiPost<Record<string, unknown>>("/api/v1/edc/transfers", payload);
}

export function advanceTransfer(id: string, action: string, payload?: Record<string, unknown>) {
  return apiPost<Record<string, unknown>>(`/api/v1/edc/transfers/${id}/${action}`, payload ?? {});
}
