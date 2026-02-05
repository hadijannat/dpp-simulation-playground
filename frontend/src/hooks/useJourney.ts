import { useMutation, useQuery } from "@tanstack/react-query";
import {
  applyComplianceFix,
  createJourneyRun,
  executeJourneyStep,
  getComplianceRun,
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

export function useCsatFeedback() {
  return useMutation({
    mutationFn: (payload: { score: number; locale: string; role: string; flow: string; comment?: string }) =>
      submitCsat(payload),
  });
}
