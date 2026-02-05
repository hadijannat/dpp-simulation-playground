from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...schemas.v2 import CsatFeedback, CsatFeedbackResponse

router = APIRouter()


FEEDBACK: Dict[str, dict] = {}


@router.post("/feedback/csat", response_model=CsatFeedbackResponse)
def submit_csat(request: Request, payload: CsatFeedback):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    feedback_id = str(uuid4())
    item = {
        "id": feedback_id,
        "score": payload.score,
        "locale": payload.locale,
        "role": payload.role,
        "flow": payload.flow,
        "comment": payload.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    FEEDBACK[feedback_id] = item
    return item
