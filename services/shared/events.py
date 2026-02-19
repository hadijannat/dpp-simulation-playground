from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

STORY_STEP_COMPLETED = "story_step_completed"
STORY_COMPLETED = "story_completed"
STORY_FAILED = "story_failed"
EPIC_COMPLETED = "epic_completed"
COMPLIANCE_CHECK_PASSED = "compliance_check_passed"
API_CALL_SUCCESS = "api_call_success"
AAS_CREATED = "aas_created"
AAS_UPDATED = "aas_updated"
AAS_SUBMODEL_ADDED = "aas_submodel_added"
AAS_SUBMODEL_PATCHED = "aas_submodel_patched"
AASX_UPLOADED = "aasx_uploaded"
EDC_NEGOTIATION_COMPLETED = "edc_negotiation_completed"
EDC_TRANSFER_COMPLETED = "edc_transfer_completed"
EDC_NEGOTIATION_STATE_CHANGED = "edc_negotiation_state_changed"
EDC_TRANSFER_STATE_CHANGED = "edc_transfer_state_changed"
GAP_REPORTED = "gap_reported"
EVENT_SCHEMA_VERSION = "1"

REQUIRED_EVENT_FIELDS = (
    "event_id",
    "event_type",
    "user_id",
    "timestamp",
    "source_service",
    "version",
)


class EventEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: str
    user_id: str
    timestamp: str
    source_service: str
    version: str = EVENT_SCHEMA_VERSION

    session_id: str | None = None
    run_id: str | None = None
    request_id: str | None = None
    story_code: str | None = None
    metadata: dict[str, Any] | list[Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_required_strings(self):
        for field in ("event_id", "event_type", "timestamp", "source_service", "version"):
            value = getattr(self, field)
            if not str(value).strip():
                raise ValueError(f"empty field: {field}")
        return self


def build_event(
    event_type: str,
    *,
    user_id: str | None,
    source_service: str | None = None,
    session_id: str | None = None,
    run_id: str | None = None,
    request_id: str | None = None,
    story_code: str | None = None,
    metadata: dict[str, Any] | list[Any] | None = None,
    event_id: str | None = None,
    version: str = EVENT_SCHEMA_VERSION,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_id": event_id or str(uuid4()),
        "event_type": event_type,
        "user_id": user_id or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_service": source_service or "unknown",
        "version": version,
    }
    if request_id:
        payload["request_id"] = request_id
    if session_id:
        payload["session_id"] = session_id
    if run_id:
        payload["run_id"] = run_id
    if story_code:
        payload["story_code"] = story_code
    if metadata is not None:
        payload["metadata"] = metadata
    payload.update(extra)

    # Normalize to the canonical schema while preserving additional metadata keys.
    envelope = EventEnvelopeV1.model_validate(payload)
    return envelope.model_dump(exclude_none=True)


def validate_event(event: dict[str, Any]) -> tuple[bool, str | None]:
    try:
        EventEnvelopeV1.model_validate(event)
    except ValidationError as exc:
        first = exc.errors()[0] if exc.errors() else {"msg": "invalid event payload"}
        return False, str(first.get("msg", "invalid event payload"))
    return True, None
