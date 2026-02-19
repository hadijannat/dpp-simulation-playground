from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from services.shared.models.dpp_instance import DppInstance
from services.shared.models.session import SimulationSession
from services.shared.repositories import digital_twin_repo
from services.shared.repositories import journey_repo


def _safe_uuid(value: str | None) -> UUID | None:
    """Convert a string to UUID, returning None if invalid or absent."""
    if not value:
        return None
    try:
        return UUID(value) if isinstance(value, str) else value
    except (ValueError, AttributeError):
        return None


router = APIRouter()
logger = logging.getLogger(__name__)

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


class RunCreateRequest(BaseModel):
    template_code: str = "manufacturer-core-e2e"
    role: str = "manufacturer"
    locale: str = "en"
    metadata: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None


class StepExecuteRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


def _serialize_run(run, step_runs=None, template_code: str | None = None) -> dict:
    steps = []
    if step_runs:
        for sr in step_runs:
            steps.append(
                {
                    "step_id": sr.step_key,
                    "status": sr.status or "completed",
                    "payload": sr.payload or {},
                    "metadata": sr.metadata_ or {},
                    "executed_at": sr.executed_at.isoformat() if sr.executed_at else "",
                }
            )
    return {
        "id": str(run.id),
        "template_code": template_code or "",
        "role": run.active_role,
        "locale": run.locale or "en",
        "status": run.status or "active",
        "current_step": run.current_step_key or "",
        "steps": steps,
        "metadata": run.metadata_ or {},
        "created_at": run.started_at.isoformat() if run.started_at else "",
        "updated_at": run.updated_at.isoformat() if run.updated_at else "",
    }


def _serialize_template(template, steps=None) -> dict:
    result = {
        "id": str(template.id),
        "code": template.code,
        "name": template.name,
        "description": template.description or "",
        "target_role": template.target_role,
        "is_active": template.is_active,
    }
    if steps is not None:
        result["steps"] = [
            {
                "id": str(s.id),
                "step_key": s.step_key,
                "title": s.title,
                "action": s.action,
                "order_index": s.order_index,
                "help_text": s.help_text or "",
                "default_payload": s.default_payload or {},
            }
            for s in steps
        ]
    return result


@router.post("/core/journeys/runs")
def create_run(
    request: Request, payload: RunCreateRequest, db: Session = Depends(get_db)
):
    require_roles(request.state.user, ALL_ROLES)
    template = journey_repo.get_template_by_code(db, payload.template_code)
    if not template:
        raise HTTPException(
            status_code=404, detail=f"Template '{payload.template_code}' not found"
        )
    user_id = _safe_uuid(getattr(request.state, "user", {}).get("sub"))
    run = journey_repo.create_run(
        db,
        template_id=template.id,
        user_id=user_id,
        role=payload.role,
        locale=payload.locale,
        metadata=payload.metadata,
        session_id=_safe_uuid(payload.session_id),
    )
    db.commit()
    return _serialize_run(run, template_code=template.code)


@router.get("/core/journeys/runs/{run_id}")
def get_run(request: Request, run_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    data = journey_repo.get_run_with_steps(db, UUID(run_id))
    if not data:
        raise HTTPException(status_code=404, detail="Run not found")
    run = data["run"]
    template = (
        db.query(journey_repo.JourneyTemplate).filter_by(id=run.template_id).first()
    )
    return _serialize_run(
        run, data["step_runs"], template_code=template.code if template else ""
    )


@router.post("/core/journeys/runs/{run_id}/steps/{step_id}/execute")
def execute_step(
    request: Request,
    run_id: str,
    step_id: str,
    payload: StepExecuteRequest,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)
    run = journey_repo.get_run(db, UUID(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    step_run = journey_repo.create_step_run(
        db,
        run_id=run.id,
        step_key=step_id,
        payload=payload.payload,
        metadata=payload.metadata,
    )
    # Advance to next step
    template_steps = journey_repo.list_steps_for_template(db, run.template_id)
    current_idx = next(
        (i for i, s in enumerate(template_steps) if s.step_key == step_id), -1
    )
    next_step_key = (
        template_steps[current_idx + 1].step_key
        if current_idx + 1 < len(template_steps)
        else "done"
    )
    journey_repo.update_run_step(db, run, next_step_key)

    # Best-effort digital twin snapshot capture for run-linked DPPs.
    if run.session_id:
        dpp_instance = (
            db.query(DppInstance)
            .filter(DppInstance.session_id == run.session_id)
            .order_by(DppInstance.created_at.desc())
            .first()
        )
        if dpp_instance:
            session = (
                db.query(SimulationSession)
                .filter(SimulationSession.id == run.session_id)
                .first()
            )
            session_state = (
                session.session_state
                if session and isinstance(session.session_state, dict)
                else {}
            )
            try:
                digital_twin_repo.capture_snapshot_for_dpp(
                    db,
                    dpp_instance=dpp_instance,
                    label=f"Run {run.id} step {step_id}",
                    metadata={
                        "source": "platform-core.journeys.execute_step",
                        "run_id": str(run.id),
                        "step_id": step_id,
                        "step_status": step_run.status or "completed",
                    },
                    session_state=session_state,
                )
            except (
                Exception
            ):  # pragma: no cover - failure should not block step progression
                logger.exception(
                    "Failed to capture digital twin snapshot",
                    extra={"run_id": str(run.id), "step_id": step_id},
                )
    db.commit()

    return {
        "run_id": str(run.id),
        "execution": {
            "step_id": step_run.step_key,
            "status": step_run.status or "completed",
            "payload": step_run.payload or {},
            "metadata": step_run.metadata_ or {},
            "executed_at": step_run.executed_at.isoformat()
            if step_run.executed_at
            else "",
        },
        "next_step": next_step_key,
    }


@router.get("/core/journeys/templates")
def list_templates(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    templates = journey_repo.list_active_templates(db)
    return {"items": [_serialize_template(t) for t in templates]}


@router.get("/core/journeys/templates/{code}")
def get_template(request: Request, code: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    template = journey_repo.get_template_by_code(db, code)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{code}' not found")
    steps = journey_repo.list_steps_for_template(db, template.id)
    return _serialize_template(template, steps)
