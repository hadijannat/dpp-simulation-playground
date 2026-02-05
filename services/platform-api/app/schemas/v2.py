from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str | None = None


class StoryStep(BaseModel):
    action: str
    params: dict[str, Any] | None = None


class StoryItem(BaseModel):
    code: str
    title: str
    description: str | None = None
    steps: list[StoryStep] = Field(default_factory=list)
    epic_code: str | None = None
    order_index: int | None = None
    roles: list[str] = Field(default_factory=list)
    difficulty: str | None = None


class StoryListResponse(BaseModel):
    items: list[StoryItem] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    role: str
    state: dict[str, Any] = Field(default_factory=dict)


class SessionUpdateRequest(BaseModel):
    role: str | None = None
    state: dict[str, Any] | None = None
    is_active: bool | None = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    role: str
    state: dict[str, Any] = Field(default_factory=dict)


class StoryStartResponse(BaseModel):
    session_id: str
    story: StoryItem
    status: str
    progress_id: str | None = None


class StepExecuteRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StepExecuteResponse(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)


class StoryValidateRequest(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    regulations: list[str] = Field(default_factory=list)


class StoryValidateResponse(BaseModel):
    session_id: str
    story_code: str
    result: dict[str, Any] = Field(default_factory=dict)


class ProgressItem(BaseModel):
    id: str
    story_id: int | None = None
    status: str
    completion_percentage: int
    steps_completed: list[int] = Field(default_factory=list)


class ProgressResponse(BaseModel):
    progress: list[ProgressItem] = Field(default_factory=list)


class EpicProgressItem(BaseModel):
    epic_id: int | None = None
    total_stories: int
    completed_stories: int
    completion_percentage: int


class EpicProgressResponse(BaseModel):
    epics: list[EpicProgressItem] = Field(default_factory=list)


class AasCreateRequest(BaseModel):
    aas_identifier: str
    product_name: str | None = None
    product_identifier: str | None = None
    product_category: str | None = None
    session_id: str | None = None


class AasShellListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class AasShellCreateResponse(BaseModel):
    status: str
    shell: dict[str, Any] | None = None
    error: str | None = None


class AasSubmodelCreateRequest(BaseModel):
    submodel: dict[str, Any] = Field(default_factory=dict)


class AasSubmodelCreateResponse(BaseModel):
    status: str
    submodel: dict[str, Any] | None = None
    error: str | None = None


class AasSubmodelPatchRequest(BaseModel):
    elements: list[dict[str, Any]] = Field(default_factory=list)


class AasSubmodelPatchResponse(BaseModel):
    status: str
    submodel_id: str
    elements: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class AasxUploadRequest(BaseModel):
    filename: str
    content_base64: str
    session_id: str | None = None


class AasxUploadResponse(BaseModel):
    status: str
    filename: str | None = None
    bytes: int | None = None
    storage: dict[str, Any] | None = None


class ComplianceIssue(BaseModel):
    id: str | None = None
    message: str | None = None
    regulation: str | None = None
    jsonpath: str | None = None
    severity: str | None = None
    level: str | None = None
    path: str | None = None


class ComplianceSummary(BaseModel):
    violations: int = 0
    warnings: int = 0
    recommendations: int = 0


class ComplianceRunCreate(BaseModel):
    dpp_id: str | None = None
    regulations: list[str] = Field(default_factory=lambda: ["ESPR", "Battery Regulation", "WEEE", "RoHS"])
    payload: dict[str, Any] = Field(default_factory=dict)


class ComplianceRunResponse(BaseModel):
    id: str
    status: str
    dpp_id: str | None = None
    regulations: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    violations: list[ComplianceIssue] = Field(default_factory=list)
    warnings: list[ComplianceIssue] = Field(default_factory=list)
    recommendations: list[ComplianceIssue] = Field(default_factory=list)
    summary: ComplianceSummary | None = None
    created_at: datetime | str
    updated_at: datetime | str


class ComplianceFixRequest(BaseModel):
    path: str
    value: Any


class ComplianceFixResponse(BaseModel):
    run_id: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ComplianceReportSummary(BaseModel):
    id: str
    session_id: str | None = None
    story_code: str | None = None
    status: str
    regulations: list[str] | None = None
    created_at: str | None = None


class ComplianceReportListResponse(BaseModel):
    reports: list[ComplianceReportSummary] = Field(default_factory=list)


class ComplianceReportDetail(ComplianceReportSummary):
    report: dict[str, Any] = Field(default_factory=dict)


class EDCStateTransition(BaseModel):
    state: str
    timestamp: str


class CatalogAsset(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    description: str | None = None


class CatalogResponse(BaseModel):
    dataset: list[CatalogAsset] = Field(default_factory=list)


class ParticipantItem(BaseModel):
    participant_id: str
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParticipantListResponse(BaseModel):
    items: list[ParticipantItem] = Field(default_factory=list)


class AssetItem(BaseModel):
    asset_id: str
    name: str | None = None
    policy_odrl: dict[str, Any] | None = None
    data_address: dict[str, Any] | None = None


class AssetListResponse(BaseModel):
    items: list[AssetItem] = Field(default_factory=list)


class NegotiationCreate(BaseModel):
    asset_id: str
    consumer_id: str
    provider_id: str
    policy: dict[str, Any] = Field(default_factory=dict)


class NegotiationResponse(BaseModel):
    id: str
    state: str
    policy: dict[str, Any] = Field(default_factory=dict)
    asset_id: str | None = None
    consumer_id: str | None = None
    provider_id: str | None = None
    state_history: list[EDCStateTransition] = Field(default_factory=list)
    session_id: str | None = None


class TransferCreate(BaseModel):
    asset_id: str
    consumer_id: str | None = None
    provider_id: str | None = None


class TransferResponse(BaseModel):
    id: str
    state: str
    asset_id: str | None = None
    consumer_id: str | None = None
    provider_id: str | None = None
    state_history: list[EDCStateTransition] = Field(default_factory=list)
    session_id: str | None = None


class AchievementItem(BaseModel):
    id: int | None = None
    code: str
    name: str | None = None
    description: str | None = None
    points: int | None = None
    category: str | None = None
    rarity: str | None = None
    icon_url: str | None = None


class AchievementListResponse(BaseModel):
    items: list[AchievementItem] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    user_id: str
    total_points: int
    level: int


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardEntry] = Field(default_factory=list)


class StreakEntry(BaseModel):
    user_id: str
    current_streak_days: int
    longest_streak_days: int


class StreakResponse(BaseModel):
    items: list[StreakEntry] = Field(default_factory=list)


class AnnotationCreate(BaseModel):
    story_id: int | None = None
    target_element: str | None = None
    annotation_type: str = "comment"
    content: str


class AnnotationItem(BaseModel):
    id: str
    story_id: int | None = None
    target_element: str | None = None
    annotation_type: str | None = None
    content: str
    status: str | None = None
    votes_count: int | None = None
    created_at: str | None = None


class AnnotationListResponse(BaseModel):
    items: list[AnnotationItem] = Field(default_factory=list)


class GapCreate(BaseModel):
    story_id: int | None = None
    description: str


class GapItem(BaseModel):
    id: str
    story_id: int | None = None
    description: str
    status: str | None = None
    votes_count: int | None = None
    created_at: str | None = None


class GapListResponse(BaseModel):
    items: list[GapItem] = Field(default_factory=list)


class VoteCreate(BaseModel):
    target_id: str
    value: int


class VoteItem(BaseModel):
    id: str
    target_id: str
    value: int
    created_at: str | None = None


class VoteListResponse(BaseModel):
    items: list[VoteItem] = Field(default_factory=list)


class JourneyRunCreate(BaseModel):
    template_code: str = Field(default="manufacturer-core-e2e")
    role: str = Field(default="manufacturer")
    locale: str = Field(default="en")
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyStepExecution(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyStepResult(BaseModel):
    step_id: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    executed_at: str


class JourneyRunResponse(BaseModel):
    id: str
    template_code: str
    role: str
    locale: str
    status: str
    current_step: str
    steps: list[JourneyStepResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class JourneyStepExecuteResponse(BaseModel):
    run_id: str
    execution: JourneyStepResult
    next_step: str


class DigitalTwinNode(BaseModel):
    id: str
    label: str
    type: str


class DigitalTwinEdge(BaseModel):
    id: str
    source: str
    target: str


class DigitalTwinResponse(BaseModel):
    dpp_id: str
    nodes: list[DigitalTwinNode] = Field(default_factory=list)
    edges: list[DigitalTwinEdge] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class CsatFeedback(BaseModel):
    score: int = Field(ge=1, le=5)
    locale: str = "en"
    role: str = "manufacturer"
    flow: str = "manufacturer-core-e2e"
    comment: str | None = None


class CsatFeedbackResponse(BaseModel):
    id: str
    score: int
    locale: str
    role: str
    flow: str
    comment: str | None = None
    created_at: str
