from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...config import COMPLIANCE_URL, PLATFORM_CORE_URL
from ...core.proxy import request_json

router = APIRouter()

COMPLIANCE_ROLES = ["manufacturer", "developer", "admin", "regulator"]


class ComplianceRunCreate(BaseModel):
    dpp_id: str | None = None
    regulations: list[str] = Field(default_factory=lambda: ["ESPR", "Battery Regulation", "WEEE", "RoHS"])
    payload: dict[str, Any] = Field(default_factory=dict)


class ComplianceFixRequest(BaseModel):
    path: str
    value: Any


@router.post("/compliance/runs")
def create_run(request: Request, payload: ComplianceRunCreate):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return request_json(
        request,
        "POST",
        f"{PLATFORM_CORE_URL}/api/v2/core/compliance/runs",
        json_body=payload.model_dump(),
    )


@router.get("/compliance/runs/{run_id}")
def get_run(request: Request, run_id: str):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/compliance/runs/{run_id}")


@router.post("/compliance/runs/{run_id}/apply-fix")
def apply_fix(request: Request, run_id: str, payload: ComplianceFixRequest):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return request_json(
        request,
        "POST",
        f"{PLATFORM_CORE_URL}/api/v2/core/compliance/runs/{run_id}/apply-fix",
        json_body=payload.model_dump(),
    )


@router.get("/compliance/reports")
def list_reports(
    request: Request,
    session_id: str | None = None,
    story_code: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    params = {"session_id": session_id, "story_code": story_code, "status": status, "limit": limit}
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports", params=clean_params)
    return {"reports": payload.get("reports", [])}


@router.get("/compliance/reports/{report_id}")
def get_report(request: Request, report_id: str):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    return request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports/{report_id}")
