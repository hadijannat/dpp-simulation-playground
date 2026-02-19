from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...config import AAS_ADAPTER_URL
from ...core.aasx_storage import store_aasx_payload
from ...core.db import get_db
from ...core.event_publisher import publish_event
from ...models.dpp_instance import DppInstance
from ...models.validation_result import ValidationResult
from ...schemas.aas_schema import (
    AasCreate,
    AasSubmodelCreate,
    AasSubmodelElementsPatch,
    AasValidateRequest,
    AasxUploadRequest,
)
from services.shared import events
from services.shared.user_registry import resolve_user_id

router = APIRouter()

TRACE_HEADERS = ("traceparent", "tracestate", "baggage")


def _mark_deprecated(response: Response, successor_path: str) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Warning"] = f'299 - "Deprecated endpoint; use {successor_path}"'
    response.headers["Link"] = f"<{successor_path}>; rel=\"successor-version\""


def _adapter_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if request_id:
        headers["X-Request-ID"] = str(request_id)
    for header in TRACE_HEADERS:
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


def _adapter_json(
    request: Request,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
) -> dict:
    try:
        response = requests.request(
            method=method,
            url=f"{AAS_ADAPTER_URL}{path}",
            json=json_body,
            headers=_adapter_headers(request),
            timeout=8,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"AAS adapter unavailable: {exc}") from exc

    payload: dict | list | str = {}
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}

    if not response.ok:
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error") or payload
        else:
            detail = payload or "AAS adapter request failed"
        raise HTTPException(status_code=response.status_code, detail=detail)

    if isinstance(payload, dict):
        return payload
    return {"items": payload}


@router.post("/aas/shells")
def create_shell(request: Request, payload: AasCreate, response: Response, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    _mark_deprecated(response, "/api/v2/aas/shells")
    adapter_payload = {
        "aas_identifier": payload.aas_identifier,
        "product_name": payload.product_name,
        "product_identifier": payload.product_identifier,
    }
    adapter_response = _adapter_json(request, "POST", "/api/v2/aas/shells", json_body=adapter_payload)
    status = adapter_response.get("status", "created")
    shell = adapter_response.get("shell") or adapter_response.get("aas") or adapter_payload

    dpp = DppInstance(
        id=uuid4(),
        session_id=payload.session_id,
        aas_identifier=payload.aas_identifier,
        product_identifier=payload.product_identifier,
        product_name=payload.product_name,
        product_category=payload.product_category,
        compliance_status={},
    )
    try:
        db.add(dpp)
        db.commit()
    except Exception:
        db.rollback()
    return {"status": status, "aas": shell, "error": adapter_response.get("error")}

@router.get("/aas/shells")
def list_shells(request: Request, response: Response):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    _mark_deprecated(response, "/api/v2/aas/shells")
    return _adapter_json(request, "GET", "/api/v2/aas/shells")

@router.post("/aas/validate")
def validate_aas(request: Request, payload: AasValidateRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    candidate_dirs = []
    env_dir = os.getenv("IDTA_TEMPLATES_DIR")
    if env_dir:
        candidate_dirs.append(Path(env_dir))
    resolved = Path(__file__).resolve()
    for idx in (5, 3):
        try:
            candidate_dirs.append(resolved.parents[idx] / "data" / "idta-templates")
        except IndexError:
            continue
    templates_dir = next((p for p in candidate_dirs if p.exists()), Path("/app/data/idta-templates"))
    missing_templates = []
    for template in payload.templates:
        if not (templates_dir / template).exists():
            missing_templates.append(template)
    status = "ok" if not missing_templates else "missing_templates"
    result = {"status": status, "missing_templates": missing_templates}
    record = ValidationResult(id=str(uuid4()), result=result)
    db.add(record)
    db.commit()
    return result


@router.post("/aas/submodels")
def create_submodel(request: Request, payload: AasSubmodelCreate, response: Response):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    _mark_deprecated(response, "/api/v2/aas/submodels")
    adapter_response = _adapter_json(
        request,
        "POST",
        "/api/v2/aas/submodels",
        json_body={"submodel": payload.submodel},
    )
    return {
        "status": adapter_response.get("status", "created"),
        "submodel": adapter_response.get("submodel", payload.submodel),
        "error": adapter_response.get("error"),
    }


@router.get("/aas/submodels/{submodel_id}/elements")
def get_submodel_elements(request: Request, submodel_id: str, response: Response):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    _mark_deprecated(response, f"/api/v2/aas/submodels/{submodel_id}/elements")
    return _adapter_json(request, "GET", f"/api/v2/aas/submodels/{submodel_id}/elements")


@router.patch("/aas/submodels/{submodel_id}/elements")
def patch_submodel_elements(
    request: Request,
    submodel_id: str,
    payload: AasSubmodelElementsPatch,
    response: Response,
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    _mark_deprecated(response, f"/api/v2/aas/submodels/{submodel_id}/elements")
    adapter_response = _adapter_json(
        request,
        "PATCH",
        f"/api/v2/aas/submodels/{submodel_id}/elements",
        json_body={"elements": payload.elements},
    )
    return {
        "status": adapter_response.get("status", "updated"),
        "elements": adapter_response.get("elements", payload.elements),
        "error": adapter_response.get("error"),
    }


@router.post("/aasx/upload")
def upload_aasx(request: Request, payload: AasxUploadRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    stored = store_aasx_payload(
        db=db,
        session_id=payload.session_id,
        filename=payload.filename,
        content_base64=payload.content_base64,
        metadata={"source": "api"},
    )
    user_id = resolve_user_id(db, request.state.user)
    publish_event(
        "simulation.events",
        events.build_event(
            events.AASX_UPLOADED,
            user_id=user_id or "",
            source_service="simulation-engine",
            request_id=getattr(request.state, "request_id", None),
            session_id=payload.session_id,
            metadata={"source": "api"},
        ),
    )
    return {"status": "stored", "storage": stored}
