import { useMutation, useQuery } from "@tanstack/react-query";
import {
  applyComplianceFix,
  createJourneyRun,
  executeJourneyStep,
  getComplianceRun,
  getDigitalTwinDiff,
  getDigitalTwinHistory,
  getDigitalTwin,
  getJourneyRun,
  runCompliance,
  submitCsat,
} from "../services/platformV2Service";

export function useJourneyRun(runId?: string) {
  const run = useQuery({
    queryKey: ["journey-run", runId],
    queryFn: () => getJourneyRun(runId || ""),
    enabled: Boolean(runId),
  });

  const createRun = useMutation({
    mutationFn: (payload: { template_code?: string; role: string; locale: string; metadata?: Record<string, unknown> }) =>
      createJourneyRun(payload),
  });

  const executeStep = useMutation({
    mutationFn: (payload: { runId: string; stepId: string; body: { payload: Record<string, unknown>; metadata?: Record<string, unknown> } }) =>
      executeJourneyStep(payload.runId, payload.stepId, payload.body),
  });

  return { run, createRun, executeStep };
}

export function useJourneyCompliance(runId?: string) {
  const complianceRun = useQuery({
    queryKey: ["journey-compliance", runId],
    queryFn: () => getComplianceRun(runId || ""),
    enabled: Boolean(runId),
  });

  const runCheck = useMutation({
    mutationFn: (payload: { dpp_id?: string; regulations?: string[]; payload: Record<string, unknown> }) =>
      runCompliance(payload),
  });

  const applyFix = useMutation({
    mutationFn: (payload: { runId: string; path: string; value: unknown }) =>
      applyComplianceFix(payload.runId, { path: payload.path, value: payload.value }),
  });

  return { complianceRun, runCheck, applyFix };
}

export function useDigitalTwin(dppId?: string) {
  return useQuery({
    queryKey: ["digital-twin", dppId],
    queryFn: () => getDigitalTwin(dppId || ""),
    enabled: Boolean(dppId),
  });
}

export function useDigitalTwinHistory(dppId?: string, limit = 25, offset = 0) {
  return useQuery({
    queryKey: ["digital-twin-history", dppId, limit, offset],
    queryFn: () => getDigitalTwinHistory(dppId || "", limit, offset),
    enabled: Boolean(dppId),
  });
}

export function useDigitalTwinDiff(dppId?: string, fromSnapshotId?: string, toSnapshotId?: string) {
  return useQuery({
    queryKey: ["digital-twin-diff", dppId, fromSnapshotId, toSnapshotId],
    queryFn: () => getDigitalTwinDiff(dppId || "", fromSnapshotId || "", toSnapshotId || ""),
    enabled: Boolean(dppId && fromSnapshotId && toSnapshotId && fromSnapshotId !== toSnapshotId),
  });
}

export function useCsatFeedback() {
  return useMutation({
    mutationFn: (payload: { score: number; locale: string; role: string; flow: string; comment?: string }) =>
      submitCsat(payload),
  });
}
