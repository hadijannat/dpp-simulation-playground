from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import SIMULATION_URL
from ...core.proxy import request_json
from ...schemas.v2 import (
    EpicProgressResponse,
    ProgressResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionUpdateRequest,
    StepExecuteRequest,
    StepExecuteResponse,
    StoryListResponse,
    StoryStartResponse,
    StoryValidateRequest,
    StoryValidateResponse,
)

router = APIRouter()


@router.get("/simulation/stories", response_model=StoryListResponse)
def list_stories(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{SIMULATION_URL}/api/v1/stories")
    return {"items": payload.get("items", [])}


@router.post("/simulation/sessions", response_model=SessionResponse)
def create_session(request: Request, payload: SessionCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions",
        json_body=payload.model_dump(),
    )


@router.get("/simulation/sessions/{session_id}", response_model=SessionResponse)
def get_session(request: Request, session_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{SIMULATION_URL}/api/v1/sessions/{session_id}")
    return payload


@router.patch("/simulation/sessions/{session_id}", response_model=SessionResponse)
def update_session(request: Request, session_id: str, payload: SessionUpdateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return request_json(
        request,
        "PATCH",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}",
        json_body=payload.model_dump(exclude_none=True),
    )


@router.post("/simulation/sessions/{session_id}/stories/{code}/start", response_model=StoryStartResponse)
def start_story(request: Request, session_id: str, code: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/start",
        json_body={},
    )


@router.post(
    "/simulation/sessions/{session_id}/stories/{code}/steps/{idx}/execute",
    response_model=StepExecuteResponse,
)
def execute_step(
    request: Request,
    session_id: str,
    code: str,
    idx: int,
    payload: StepExecuteRequest,
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/steps/{idx}/execute",
        json_body=payload.model_dump(),
    )


@router.post(
    "/simulation/sessions/{session_id}/stories/{code}/validate",
    response_model=StoryValidateResponse,
)
def validate_story(
    request: Request,
    session_id: str,
    code: str,
    payload: StoryValidateRequest,
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/validate",
        json_body=payload.model_dump(),
    )


@router.get("/simulation/progress", response_model=ProgressResponse)
def get_progress(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{SIMULATION_URL}/api/v1/progress")
    return {"progress": payload.get("progress", [])}


@router.get("/simulation/progress/epics", response_model=EpicProgressResponse)
def get_epic_progress(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{SIMULATION_URL}/api/v1/progress/epics")
    return {"epics": payload.get("epics", [])}
