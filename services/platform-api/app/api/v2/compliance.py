from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from ...auth import require_roles
from ...config import COMPLIANCE_URL
from ...core.proxy import request_json
from ...schemas.v2 import (
    ComplianceFixRequest,
    ComplianceFixResponse,
    ComplianceReportDetail,
    ComplianceReportListResponse,
    ComplianceRunCreate,
    ComplianceRunResponse,
)

router = APIRouter()

RUNS: dict[str, dict[str, Any]] = {}


@router.post("/compliance/runs", response_model=ComplianceRunResponse)
def create_run(request: Request, payload: ComplianceRunCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])

    upstream = request_json(
        request,
        "POST",
        f"{COMPLIANCE_URL}/api/v1/compliance/check",
        json_body={
            "data": payload.payload,
            "regulations": payload.regulations,
        },
    )
    now = datetime.now(timezone.utc).isoformat()
    run_id = str(uuid4())
    run = {
        "id": run_id,
        "status": upstream.get("status", "unknown"),
        "dpp_id": payload.dpp_id,
        "regulations": payload.regulations,
        "payload": payload.payload,
        "violations": upstream.get("violations", []),
        "warnings": upstream.get("warnings", []),
        "recommendations": upstream.get("recommendations", []),
        "summary": upstream.get("summary"),
        "created_at": now,
        "updated_at": now,
    }
    RUNS[run_id] = run
    return run


@router.get("/compliance/runs/{run_id}", response_model=ComplianceRunResponse)
def get_run(request: Request, run_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Compliance run not found")
    return run


@router.post("/compliance/runs/{run_id}/apply-fix", response_model=ComplianceFixResponse)
def apply_fix(request: Request, run_id: str, payload: ComplianceFixRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Compliance run not found")

    run_payload = dict(run.get("payload") or {})
    key = payload.path.strip().lstrip("$.")
    run_payload[key] = payload.value
    run["payload"] = run_payload
    run["violations"] = [v for v in run.get("violations", []) if v.get("path") != payload.path]
    run["status"] = "compliant" if not run["violations"] else "non-compliant"
    run["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {"run_id": run_id, "status": run["status"], "payload": run_payload}


@router.get("/compliance/reports", response_model=ComplianceReportListResponse)
def list_reports(
    request: Request,
    session_id: str | None = None,
    story_code: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    params = {
        "session_id": session_id,
        "story_code": story_code,
        "status": status,
        "limit": limit,
    }
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(
        request,
        "GET",
        f"{COMPLIANCE_URL}/api/v1/reports",
        params=clean_params,
    )
    return {"reports": payload.get("reports", [])}


@router.get("/compliance/reports/{report_id}", response_model=ComplianceReportDetail)
def get_report(request: Request, report_id: str):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    payload = request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports/{report_id}")
    return payload
