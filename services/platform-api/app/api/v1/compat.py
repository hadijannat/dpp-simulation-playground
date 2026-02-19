from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import (
    AAS_ADAPTER_URL,
    COLLABORATION_URL,
    COMPLIANCE_URL,
    EDC_URL,
    GAMIFICATION_URL,
    SIMULATION_URL,
)
from ...core.proxy import request_json

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]
CREATOR_ROLES = ["manufacturer", "developer", "admin"]
COMPLIANCE_ROLES = ["manufacturer", "developer", "admin", "regulator"]
REGULATOR_ROLES = ["regulator", "developer", "admin"]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/stories")
def list_stories(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{SIMULATION_URL}/api/v1/stories")


@router.post("/sessions")
def create_session(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{SIMULATION_URL}/api/v1/sessions", json_body=payload
    )


@router.get("/sessions/{session_id}")
def get_session(request: Request, session_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "GET", f"{SIMULATION_URL}/api/v1/sessions/{session_id}"
    )


@router.patch("/sessions/{session_id}")
def patch_session(request: Request, session_id: str, payload: dict[str, Any]):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "PATCH",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}",
        json_body=payload,
    )


@router.delete("/sessions/{session_id}")
def delete_session(request: Request, session_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "DELETE", f"{SIMULATION_URL}/api/v1/sessions/{session_id}"
    )


@router.post("/sessions/{session_id}/pause")
def pause_session(request: Request, session_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{SIMULATION_URL}/api/v1/sessions/{session_id}/pause"
    )


@router.post("/sessions/{session_id}/resume")
def resume_session(request: Request, session_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{SIMULATION_URL}/api/v1/sessions/{session_id}/resume"
    )


@router.post("/sessions/{session_id}/complete")
def complete_session(request: Request, session_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{SIMULATION_URL}/api/v1/sessions/{session_id}/complete"
    )


@router.post("/sessions/{session_id}/stories/{code}/start")
def start_story(
    request: Request, session_id: str, code: str, payload: dict[str, Any] | None = None
):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/start",
        json_body=payload or {},
    )


@router.post("/sessions/{session_id}/stories/{code}/steps/{idx}/execute")
def execute_step(
    request: Request,
    session_id: str,
    code: str,
    idx: int,
    payload: dict[str, Any],
):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/steps/{idx}/execute",
        json_body=payload,
    )


@router.post("/sessions/{session_id}/stories/{code}/validate")
def validate_story(
    request: Request,
    session_id: str,
    code: str,
    payload: dict[str, Any],
):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request,
        "POST",
        f"{SIMULATION_URL}/api/v1/sessions/{session_id}/stories/{code}/validate",
        json_body=payload,
    )


@router.get("/progress")
def get_progress(
    request: Request,
    session_id: str | None = None,
    role: str | None = None,
    status: str | None = None,
    story_code: str | None = None,
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ALL_ROLES)
    params = {
        "session_id": session_id,
        "role": role,
        "status": status,
        "story_code": story_code,
        "user_id": user_id,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {key: value for key, value in params.items() if value is not None}
    return request_json(
        request, "GET", f"{SIMULATION_URL}/api/v1/progress", params=clean_params
    )


@router.get("/progress/epics")
def get_epic_progress(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{SIMULATION_URL}/api/v1/progress/epics")


@router.get("/aas/shells")
def list_shells(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{AAS_ADAPTER_URL}/api/v2/aas/shells")


@router.post("/aas/shells")
def create_shell(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, CREATOR_ROLES)
    asset_information = payload.get("assetInformation")
    global_asset_id = (
        asset_information.get("globalAssetId")
        if isinstance(asset_information, dict)
        else None
    )
    adapter_payload = {
        "aas_identifier": payload.get("aas_identifier") or payload.get("id"),
        "product_name": payload.get("product_name") or payload.get("idShort"),
        "product_identifier": payload.get("product_identifier") or global_asset_id,
    }
    return request_json(
        request,
        "POST",
        f"{AAS_ADAPTER_URL}/api/v2/aas/shells",
        json_body=adapter_payload,
    )


@router.post("/aas/submodels")
def create_submodel(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, CREATOR_ROLES)
    body = {"submodel": payload.get("submodel") or payload}
    return request_json(
        request, "POST", f"{AAS_ADAPTER_URL}/api/v2/aas/submodels", json_body=body
    )


@router.get("/aas/submodels/{submodel_id}/elements")
def get_submodel_elements(request: Request, submodel_id: str):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "GET", f"{AAS_ADAPTER_URL}/api/v2/aas/submodels/{submodel_id}/elements"
    )


@router.patch("/aas/submodels/{submodel_id}/elements")
def patch_submodel_elements(
    request: Request, submodel_id: str, payload: dict[str, Any]
):
    require_roles(request.state.user, CREATOR_ROLES)
    body = {"elements": payload.get("elements", payload)}
    return request_json(
        request,
        "PATCH",
        f"{AAS_ADAPTER_URL}/api/v2/aas/submodels/{submodel_id}/elements",
        json_body=body,
    )


@router.post("/aas/validate")
def validate_aas(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, REGULATOR_ROLES)
    return request_json(
        request, "POST", f"{SIMULATION_URL}/api/v1/aas/validate", json_body=payload
    )


@router.post("/aasx/upload")
def upload_aasx(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, CREATOR_ROLES)
    body = {
        "filename": payload.get("filename"),
        "content_base64": payload.get("content_base64"),
    }
    return request_json(
        request, "POST", f"{AAS_ADAPTER_URL}/api/v2/aasx/upload", json_body=body
    )


@router.post("/compliance/check")
def check_compliance(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return request_json(
        request, "POST", f"{COMPLIANCE_URL}/api/v1/compliance/check", json_body=payload
    )


@router.get("/reports")
def list_reports(
    request: Request,
    session_id: str | None = None,
    story_code: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    require_roles(request.state.user, REGULATOR_ROLES)
    params = {
        "session_id": session_id,
        "story_code": story_code,
        "status": status,
        "limit": limit,
    }
    clean_params = {key: value for key, value in params.items() if value is not None}
    return request_json(
        request, "GET", f"{COMPLIANCE_URL}/api/v1/reports", params=clean_params
    )


@router.get("/reports/{report_id}")
def get_report(request: Request, report_id: str):
    require_roles(request.state.user, REGULATOR_ROLES)
    return request_json(request, "GET", f"{COMPLIANCE_URL}/api/v1/reports/{report_id}")


@router.get("/edc/catalog")
def get_catalog(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{EDC_URL}/api/v1/edc/catalog")


@router.get("/edc/participants")
def get_participants(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{EDC_URL}/api/v1/edc/participants")


@router.get("/edc/assets")
def get_assets(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{EDC_URL}/api/v1/edc/assets")


@router.post("/edc/negotiations")
def create_negotiation(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, CREATOR_ROLES)
    return request_json(
        request, "POST", f"{EDC_URL}/api/v1/edc/negotiations", json_body=payload
    )


@router.post("/edc/negotiations/{negotiation_id}/{action}")
def negotiation_action(
    request: Request,
    negotiation_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
):
    require_roles(request.state.user, CREATOR_ROLES)
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/negotiations/{negotiation_id}/{action}",
        json_body=payload or {},
    )


@router.post("/edc/transfers")
def create_transfer(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, CREATOR_ROLES)
    return request_json(
        request, "POST", f"{EDC_URL}/api/v1/edc/transfers", json_body=payload
    )


@router.post("/edc/transfers/{transfer_id}/{action}")
def transfer_action(
    request: Request,
    transfer_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
):
    require_roles(request.state.user, CREATOR_ROLES)
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/transfers/{transfer_id}/{action}",
        json_body=payload or {},
    )


@router.get("/achievements")
def list_achievements(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{GAMIFICATION_URL}/api/v1/achievements")


@router.get("/leaderboard")
def leaderboard(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    window: str = "all",
    role: str | None = None,
):
    require_roles(request.state.user, ALL_ROLES)
    params = {"limit": limit, "offset": offset, "window": window}
    if role is not None:
        params["role"] = role
    return request_json(
        request,
        "GET",
        f"{GAMIFICATION_URL}/api/v1/leaderboard",
        params=params,
    )


@router.get("/streaks")
def streaks(request: Request):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(request, "GET", f"{GAMIFICATION_URL}/api/v1/streaks")


@router.get("/annotations")
def list_annotations(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    target_element: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ALL_ROLES)
    params = {
        "story_id": story_id,
        "status": status,
        "target_element": target_element,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {key: value for key, value in params.items() if value is not None}
    return request_json(
        request, "GET", f"{COLLABORATION_URL}/api/v1/annotations", params=clean_params
    )


@router.post("/annotations")
def add_annotation(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{COLLABORATION_URL}/api/v1/annotations", json_body=payload
    )


@router.get("/gap_reports")
def gap_reports(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ALL_ROLES)
    params = {
        "story_id": story_id,
        "status": status,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {key: value for key, value in params.items() if value is not None}
    return request_json(
        request, "GET", f"{COLLABORATION_URL}/api/v1/gap_reports", params=clean_params
    )


@router.post("/gap_reports")
def add_gap_report(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{COLLABORATION_URL}/api/v1/gap_reports", json_body=payload
    )


@router.get("/votes")
def votes(
    request: Request, target_id: str | None = None, limit: int = 50, offset: int = 0
):
    require_roles(request.state.user, ALL_ROLES)
    params = {"target_id": target_id, "limit": limit, "offset": offset}
    clean_params = {key: value for key, value in params.items() if value is not None}
    return request_json(
        request, "GET", f"{COLLABORATION_URL}/api/v1/votes", params=clean_params
    )


@router.post("/votes")
def vote(request: Request, payload: dict[str, Any]):
    require_roles(request.state.user, ALL_ROLES)
    return request_json(
        request, "POST", f"{COLLABORATION_URL}/api/v1/votes", json_body=payload
    )
