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

export interface JourneyStepDefinition {
  id: string;
  step_key: string;
  title: string;
  action: string;
  order_index: number;
  help_text: string;
  default_payload: Record<string, unknown>;
}

export interface JourneyTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  target_role: string;
  is_active: boolean;
  steps?: JourneyStepDefinition[];
}
