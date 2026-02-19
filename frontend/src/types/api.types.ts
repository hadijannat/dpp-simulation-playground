import type { components } from "./generated/platform-api";

type Schemas = components["schemas"];

export type HealthResponse = Schemas["HealthResponse"];

export type StoryStep = Omit<Schemas["StoryStep"], "params"> & {
  params?: Record<string, unknown>;
};

export type Story = Omit<Schemas["StoryItem"], "description" | "steps" | "epic_code" | "difficulty"> & {
  description?: string;
  steps: StoryStep[];
  epic_code?: string;
  difficulty?: string;
};

export type StoryListResponse = {
  items: Story[];
};

export type SessionResponse = Omit<Schemas["SessionResponse"], "state"> & {
  state: Record<string, unknown>;
};

export type StepExecuteResponse = Omit<Schemas["StepExecuteResponse"], "result"> & {
  result: Record<string, unknown>;
};

export type StoryValidateResponse = Omit<Schemas["StoryValidateResponse"], "result"> & {
  result: Record<string, unknown>;
};

export type ProgressItem = Omit<Schemas["ProgressItem"], "steps_completed"> & {
  steps_completed: number[];
};

export type ProgressResponse = {
  progress: ProgressItem[];
};

export type EpicProgressItem = Schemas["EpicProgressItem"];

export type EpicProgressResponse = {
  epics: EpicProgressItem[];
};

export type ComplianceRuleResult = Schemas["ComplianceIssue"];

export type ComplianceResult = Omit<
  Schemas["ComplianceRunResponse"],
  "payload" | "violations" | "warnings" | "recommendations"
> & {
  payload?: Record<string, unknown>;
  violations?: ComplianceRuleResult[];
  warnings?: ComplianceRuleResult[];
  recommendations?: ComplianceRuleResult[];
};

export type ComplianceReportSummary = Schemas["ComplianceReportSummary"];

export type ComplianceReportList = {
  reports: ComplianceReportSummary[];
};

export type LeaderboardEntry = Schemas["LeaderboardEntry"] & {
  role?: string | null;
  window?: string | null;
};

export type Achievement = Schemas["AchievementItem"];

export type LeaderboardWindow = "all" | "daily" | "weekly" | "monthly";

export type LeaderboardResponse = {
  items: LeaderboardEntry[];
  window?: LeaderboardWindow | string | null;
  role?: string | null;
};

export type StreakEntry = Schemas["StreakEntry"];

export type StreakResponse = {
  items: StreakEntry[];
};

export type CatalogAsset = Schemas["CatalogAsset"];

export type CatalogResponse = {
  dataset: CatalogAsset[];
};

export type EDCParticipant = Omit<Schemas["ParticipantItem"], "metadata"> & {
  metadata?: Record<string, unknown>;
};

export type EDCParticipantList = {
  items: EDCParticipant[];
};

export type EDCAsset = Omit<Schemas["AssetItem"], "policy_odrl" | "data_address"> & {
  policy_odrl?: Record<string, unknown> | null;
  data_address?: Record<string, unknown> | null;
};

export type EDCAssetList = {
  items: EDCAsset[];
};

export type EDCStateTransition = Schemas["EDCStateTransition"];

export type EDCNegotiation = Omit<Schemas["NegotiationResponse"], "policy"> & {
  policy?: Record<string, unknown>;
};

export type EDCTransfer = Schemas["TransferResponse"];

export type AasShellListResponse = {
  items: Record<string, unknown>[];
};

export type AasShellCreateResponse = Omit<Schemas["AasShellCreateResponse"], "shell"> & {
  shell?: Record<string, unknown> | null;
};

export type AasSubmodelCreateResponse = Omit<Schemas["AasSubmodelCreateResponse"], "submodel"> & {
  submodel?: Record<string, unknown> | null;
};

export type AasxUploadResponse = Omit<Schemas["AasxUploadResponse"], "storage"> & {
  storage?: Record<string, unknown> | null;
};
