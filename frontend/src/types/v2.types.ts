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

export type DigitalTwinNode = Schemas["DigitalTwinNode"];

export type DigitalTwinEdge = Schemas["DigitalTwinEdge"];

export type DigitalTwin = Omit<Schemas["DigitalTwinResponse"], "nodes" | "edges" | "timeline"> & {
  nodes: DigitalTwinNode[];
  edges: DigitalTwinEdge[];
  timeline: Array<Record<string, unknown>>;
};

export interface DigitalTwinSnapshotItem {
  snapshot_id: string;
  label?: string | null;
  created_at?: string | null;
  metadata: Record<string, unknown>;
  node_count: number;
  edge_count: number;
}

export interface DigitalTwinHistoryResponse {
  dpp_id: string;
  items: DigitalTwinSnapshotItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface DigitalTwinDiffChangedItem {
  key: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
}

export interface DigitalTwinDiffGroup {
  added: Array<Record<string, unknown>>;
  removed: Array<Record<string, unknown>>;
  changed: DigitalTwinDiffChangedItem[];
}

export interface DigitalTwinDiffSummary {
  nodes_added: number;
  nodes_removed: number;
  nodes_changed: number;
  edges_added: number;
  edges_removed: number;
  edges_changed: number;
}

export interface DigitalTwinDiffResult {
  summary: DigitalTwinDiffSummary;
  nodes: DigitalTwinDiffGroup;
  edges: DigitalTwinDiffGroup;
  generated_at?: string | null;
}

export interface DigitalTwinDiffResponse {
  dpp_id: string;
  from_snapshot: DigitalTwinSnapshotItem;
  to_snapshot: DigitalTwinSnapshotItem;
  diff: DigitalTwinDiffResult;
}

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
