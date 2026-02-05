from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from services.shared.repositories import feedback_repo

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


class CsatRequest(BaseModel):
    score: int = Field(ge=1, le=5)
    locale: str = "en"
    role: str = "manufacturer"
    flow: str = "manufacturer-core-e2e"
    comment: str | None = None
    journey_run_id: str | None = None


@router.post("/core/feedback/csat")
def submit_csat(request: Request, payload: CsatRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    user_id = getattr(request.state, "user", {}).get("sub")
    fb = feedback_repo.create_feedback(
        db,
        user_id=user_id,
        journey_run_id=payload.journey_run_id,
        locale=payload.locale,
        role=payload.role,
        flow=payload.flow,
        score=payload.score,
        comment=payload.comment,
    )
    return {
        "id": str(fb.id),
        "score": fb.score,
        "locale": fb.locale or "en",
        "role": fb.role,
        "flow": fb.flow,
        "comment": fb.comment,
        "created_at": fb.created_at.isoformat() if fb.created_at else "",
    }
