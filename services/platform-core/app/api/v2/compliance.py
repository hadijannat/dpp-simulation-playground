from __future__ import annotations

from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...config import COMPLIANCE_URL
from ...core.db import get_db
from services.shared.models.compliance_report import ComplianceReport
from services.shared.repositories import compliance_fix_repo

router = APIRouter()

COMPLIANCE_ROLES = ["manufacturer", "developer", "admin", "regulator"]


class ComplianceRunCreateRequest(BaseModel):
    dpp_id: str | None = None
    regulations: list[str] = Field(default_factory=lambda: ["ESPR", "Battery Regulation", "WEEE", "RoHS"])
    payload: dict[str, Any] = Field(default_factory=dict)


class ComplianceFixApplyRequest(BaseModel):
    path: str
    value: Any


@router.get("/core/compliance/status")
def compliance_status(request: Request):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return {"status": "ok", "module": "compliance"}


@router.post("/core/compliance/runs")
def create_run(request: Request, payload: ComplianceRunCreateRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    # Proxy compliance check to compliance-service
    try:
        resp = requests.post(
            f"{COMPLIANCE_URL}/api/v1/compliance/check",
            json={"data": payload.payload, "regulations": payload.regulations},
            timeout=8,
        )
        resp.raise_for_status()
        upstream = resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Compliance service unavailable: {exc}") from exc

    from uuid import uuid4
    from datetime import datetime, timezone

    user_id = getattr(request.state, "user", {}).get("sub")
    report = ComplianceReport(
        id=uuid4(),
        user_id=user_id,
        story_code=None,
        regulations=payload.regulations,
        status=upstream.get("status", "unknown"),
        report={
            "violations": upstream.get("violations", []),
            "warnings": upstream.get("warnings", []),
            "recommendations": upstream.get("recommendations", []),
            "summary": upstream.get("summary"),
            "payload": payload.payload,
            "dpp_id": payload.dpp_id,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(report.id),
        "status": report.status,
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


@router.get("/core/compliance/runs/{run_id}")
def get_run(request: Request, run_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    report = db.query(ComplianceReport).filter(ComplianceReport.id == run_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Compliance run not found")
    data = report.report or {}
    return {
        "id": str(report.id),
        "status": report.status,
        "dpp_id": data.get("dpp_id"),
        "regulations": report.regulations or [],
        "payload": data.get("payload", {}),
        "violations": data.get("violations", []),
        "warnings": data.get("warnings", []),
        "recommendations": data.get("recommendations", []),
        "summary": data.get("summary"),
        "created_at": report.created_at.isoformat() if report.created_at else "",
        "updated_at": report.created_at.isoformat() if report.created_at else "",
    }


@router.post("/core/compliance/runs/{run_id}/apply-fix")
def apply_fix(request: Request, run_id: str, payload: ComplianceFixApplyRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    report = db.query(ComplianceReport).filter(ComplianceReport.id == run_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Compliance run not found")

    user_id = getattr(request.state, "user", {}).get("sub")
    compliance_fix_repo.create_fix(db, report_id=report.id, path=payload.path, value=payload.value, applied_by=user_id)

    # Update report payload with fix
    data = dict(report.report or {})
    run_payload = dict(data.get("payload") or {})
    key = payload.path.strip().lstrip("$.")
    run_payload[key] = payload.value
    data["payload"] = run_payload
    data["violations"] = [v for v in data.get("violations", []) if v.get("path") != payload.path]
    report.report = data
    report.status = "compliant" if not data["violations"] else "non-compliant"
    db.commit()

    return {"run_id": str(report.id), "status": report.status, "payload": run_payload}
