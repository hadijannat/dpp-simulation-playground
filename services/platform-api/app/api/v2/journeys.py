from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from ...auth import require_roles
from ...schemas.v2 import (
    JourneyRunCreate,
    JourneyRunResponse,
    JourneyStepExecuteResponse,
    JourneyStepExecution,
    JourneyStepResult,
)

router = APIRouter()


RUNS: Dict[str, Dict[str, Any]] = {}


@router.post("/journeys/runs", response_model=JourneyRunResponse)
def create_run(request: Request, payload: JourneyRunCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    run_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    run = {
        "id": run_id,
        "template_code": payload.template_code,
        "role": payload.role,
        "locale": payload.locale,
        "status": "active",
        "current_step": "step-1",
        "steps": [],
        "metadata": payload.metadata,
        "created_at": now,
        "updated_at": now,
    }
    RUNS[run_id] = run
    return run


@router.get("/journeys/runs/{run_id}", response_model=JourneyRunResponse)
def get_run(request: Request, run_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/journeys/runs/{run_id}/steps/{step_id}/execute", response_model=JourneyStepExecuteResponse)
def execute_step(request: Request, run_id: str, step_id: str, payload: JourneyStepExecution):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    execution = JourneyStepResult(
        step_id=step_id,
        status="completed",
        payload=payload.payload,
        metadata=payload.metadata,
        executed_at=datetime.now(timezone.utc).isoformat(),
    )
    steps: List[Dict[str, Any]] = run.get("steps", [])
    steps.append(execution.model_dump())
    run["steps"] = steps
    run["current_step"] = f"step-{len(steps) + 1}"
    run["updated_at"] = execution.executed_at
    return {"run_id": run_id, "execution": execution, "next_step": run["current_step"]}
