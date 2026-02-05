from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

STORY_STEP_COMPLETED = "story_step_completed"
STORY_COMPLETED = "story_completed"
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
GAP_REPORTED = "gap_reported"


def build_event(
    event_type: str,
    *,
    user_id: str | None,
    session_id: str | None = None,
    story_code: str | None = None,
    metadata: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "event_type": event_type,
        "user_id": user_id or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if session_id:
        payload["session_id"] = session_id
    if story_code:
        payload["story_code"] = story_code
    if metadata:
        payload["metadata"] = metadata
    payload.update(extra)
    return payload
