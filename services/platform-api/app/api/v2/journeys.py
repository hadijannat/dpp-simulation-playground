from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...config import PLATFORM_CORE_URL
from ...core.proxy import request_json

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


class JourneyRunCreate(BaseModel):
    template_code: str = "manufacturer-core-e2e"
    role: str = "manufacturer"
    locale: str = "en"
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyStepExecution(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/journeys/runs")
def create_run(request: Request, payload: JourneyRunCreate):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs",
        json_body=payload.model_dump(),
    )


@router.get("/journeys/runs/{run_id}")
def get_run(request: Request, run_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs/{run_id}")


@router.post("/journeys/runs/{run_id}/steps/{step_id}/execute")
def execute_step(request: Request, run_id: str, step_id: str, payload: JourneyStepExecution):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs/{run_id}/steps/{step_id}/execute",
        json_body=payload.model_dump(),
    )


@router.get("/journeys/templates")
def list_templates(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/journeys/templates")


@router.get("/journeys/templates/{code}")
def get_template(request: Request, code: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/journeys/templates/{code}")
