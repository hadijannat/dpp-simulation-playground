from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, model_validator

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
    path: str | None = None
    value: Any | None = None
    operations: list["JsonPatchOperation"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payload(self):
        if self.operations:
            return self
        if not self.path:
            raise ValueError("Either operations or path must be provided")
        return self


class JsonPatchOperation(BaseModel):
    op: Literal["add", "replace", "remove"]
    path: str
    value: Any | None = None


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
    offset: int = 0,
):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    params = {"session_id": session_id, "story_code": story_code, "status": status, "limit": limit, "offset": offset}
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports", params=clean_params)
    items = payload.get("items")
    if not isinstance(items, list):
        items = payload.get("reports", [])
    total = payload.get("total")
    if not isinstance(total, int):
        total = len(items)
    resolved_limit = payload.get("limit")
    if not isinstance(resolved_limit, int):
        resolved_limit = limit
    resolved_offset = payload.get("offset")
    if not isinstance(resolved_offset, int):
        resolved_offset = offset
    return {
        "items": items,
        "total": total,
        "limit": resolved_limit,
        "offset": resolved_offset,
        # Backward-compatible alias.
        "reports": items,
    }


@router.get("/compliance/reports/{report_id}")
def get_report(request: Request, report_id: str):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    return request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports/{report_id}")
