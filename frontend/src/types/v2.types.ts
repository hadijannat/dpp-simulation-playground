import type { components } from "./generated/platform-api";

type Schemas = components["schemas"];

export type JourneyStepExecution = Omit<Schemas["JourneyStepResult"], "payload" | "metadata"> & {
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
};

export type JourneyRun = Omit<Schemas["JourneyRunResponse"], "steps" | "metadata"> & {
  steps: JourneyStepExecution[];
  metadata: Record<string, unknown>;
};

export type ComplianceRun = Omit<
  Schemas["ComplianceRunResponse"],
  "payload" | "violations" | "warnings" | "recommendations"
> & {
  payload: Record<string, unknown>;
  violations: Array<{ path?: string | null; message?: string | null; severity?: string | null }>;
  warnings: Array<{ path?: string | null; message?: string | null; severity?: string | null }>;
  recommendations: Array<{ path?: string | null; message?: string | null; severity?: string | null }>;
};

export type DigitalTwin = Omit<Schemas["DigitalTwinResponse"], "timeline"> & {
  timeline: Array<Record<string, unknown>>;
};

export type CsatFeedback = Schemas["CsatFeedbackResponse"];
