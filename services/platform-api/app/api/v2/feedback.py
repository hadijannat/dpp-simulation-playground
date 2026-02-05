from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...config import PLATFORM_CORE_URL
from ...core.proxy import request_json

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


class CsatFeedback(BaseModel):
    score: int = Field(ge=1, le=5)
    locale: str = "en"
    role: str = "manufacturer"
    flow: str = "manufacturer-core-e2e"
    comment: str | None = None


@router.post("/feedback/csat")
def submit_csat(request: Request, payload: CsatFeedback):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{PLATFORM_CORE_URL}/api/v2/core/feedback/csat",
        json_body=payload.model_dump(),
    )
