export type HealthResponse = { status: string };

export type Story = {
  code: string;
  title?: string;
  description?: string;
  steps?: unknown[];
  epic?: string;
};

export type StoryListResponse = { items: Story[] };

export type SessionResponse = {
  id: string;
  user_id: string;
  role: string;
  state: Record<string, unknown>;
};

export type ComplianceRuleResult = {
  id?: string;
  message?: string;
  regulation?: string;
  jsonpath?: string;
  severity?: string;
  level?: string;
};

export type ComplianceResult = {
  status: string;
  violations?: ComplianceRuleResult[];
  warnings?: ComplianceRuleResult[];
  recommendations?: ComplianceRuleResult[];
  summary?: {
    violations: number;
    warnings: number;
    recommendations: number;
  };
};

export type ComplianceReportSummary = {
  id: string;
  session_id?: string | null;
  story_code?: string | null;
  status: string;
  regulations?: string[];
  created_at?: string | null;
};

export type ComplianceReportList = {
  reports: ComplianceReportSummary[];
};

export type LeaderboardEntry = {
  user_id: string;
  total_points: number;
  level: number;
};

export type Achievement = {
  id?: number;
  code: string;
  name?: string;
  description?: string;
  points?: number;
  category?: string;
  rarity?: string;
  icon_url?: string;
};

export type LeaderboardResponse = {
  items: LeaderboardEntry[];
};
