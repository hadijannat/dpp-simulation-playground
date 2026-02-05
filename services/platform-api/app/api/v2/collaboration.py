from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import COLLABORATION_URL
from ...core.proxy import request_json
from ...schemas.v2 import (
    AnnotationCreate,
    AnnotationItem,
    AnnotationListResponse,
    GapCreate,
    GapItem,
    GapListResponse,
    VoteCreate,
    VoteItem,
    VoteListResponse,
)

router = APIRouter()


@router.get("/collaboration/annotations", response_model=AnnotationListResponse)
def list_annotations(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    target_element: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer", "consumer", "recycler"])
    params = {
        "story_id": story_id,
        "status": status,
        "target_element": target_element,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(
        request,
        "GET",
        f"{COLLABORATION_URL}/api/v1/annotations",
        params=clean_params,
    )
    return {"items": payload.get("items", [])}


@router.post("/collaboration/annotations", response_model=AnnotationItem)
def add_annotation(request: Request, payload: AnnotationCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    upstream = request_json(
        request,
        "POST",
        f"{COLLABORATION_URL}/api/v1/annotations",
        json_body=payload.model_dump(),
    )
    return upstream


@router.get("/collaboration/gaps", response_model=GapListResponse)
def list_gaps(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer", "consumer", "recycler"])
    params = {
        "story_id": story_id,
        "status": status,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(
        request,
        "GET",
        f"{COLLABORATION_URL}/api/v1/gap_reports",
        params=clean_params,
    )
    return {"items": payload.get("items", [])}


@router.post("/collaboration/gaps", response_model=GapItem)
def add_gap(request: Request, payload: GapCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    upstream = request_json(
        request,
        "POST",
        f"{COLLABORATION_URL}/api/v1/gap_reports",
        json_body=payload.model_dump(),
    )
    return upstream


@router.get("/collaboration/votes", response_model=VoteListResponse)
def list_votes(
    request: Request,
    target_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer", "consumer", "recycler"])
    params = {
        "target_id": target_id,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {k: v for k, v in params.items() if v is not None}
    payload = request_json(
        request,
        "GET",
        f"{COLLABORATION_URL}/api/v1/votes",
        params=clean_params,
    )
    return {"items": payload.get("items", [])}


@router.post("/collaboration/votes", response_model=VoteItem)
def vote(request: Request, payload: VoteCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    upstream = request_json(
        request,
        "POST",
        f"{COLLABORATION_URL}/api/v1/votes",
        json_body=payload.model_dump(),
    )
    return upstream
