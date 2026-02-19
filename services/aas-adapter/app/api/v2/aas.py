from typing import Dict, Any

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...config import BASYX_BASE_URL, BASYX_API_PREFIX
from services.shared.http_client import request as pooled_request

router = APIRouter()


def _api_prefix() -> str:
    return f"/{BASYX_API_PREFIX.strip('/')}" if BASYX_API_PREFIX else ""


def _basyx_request(
    method: str,
    path: str,
    *,
    json_body: Dict[str, Any] | list | None = None,
    timeout: int = 8,
) -> requests.Response:
    clean_path = path.lstrip("/")
    primary = f"{BASYX_BASE_URL}{_api_prefix()}/{clean_path}"
    response = pooled_request(
        method=method,
        url=primary,
        json=json_body,
        timeout=timeout,
        session_name="aas-adapter",
    )
    if response.status_code == 404 and _api_prefix():
        fallback = f"{BASYX_BASE_URL}/{clean_path}"
        response = pooled_request(
            method=method,
            url=fallback,
            json=json_body,
            timeout=timeout,
            session_name="aas-adapter",
        )
    response.raise_for_status()
    return response


class ShellCreateRequest(BaseModel):
    aas_identifier: str
    product_name: str | None = None
    product_identifier: str | None = None


class SubmodelCreateRequest(BaseModel):
    submodel: Dict[str, Any] = Field(default_factory=dict)


class SubmodelPatchRequest(BaseModel):
    elements: list[Dict[str, Any]] = Field(default_factory=list)


class AasxUploadRequest(BaseModel):
    filename: str
    content_base64: str


@router.get("/aas/shells")
def list_shells(request: Request):
    require_roles(
        request.state.user,
        ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"],
    )
    try:
        response = _basyx_request("GET", "shells")
        return response.json()
    except requests.RequestException:
        return {"items": []}


@router.post("/aas/shells")
def create_shell(request: Request, payload: ShellCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    shell = {
        "id": payload.aas_identifier,
        "idShort": payload.product_name or "dpp-asset",
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": payload.product_identifier or payload.aas_identifier,
        },
    }
    try:
        response = _basyx_request("POST", "shells", json_body=shell)
        return {"status": "created", "shell": response.json()}
    except requests.RequestException as exc:
        return {"status": "degraded", "shell": shell, "error": str(exc)}


@router.post("/aas/submodels")
def create_submodel(request: Request, payload: SubmodelCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    if not payload.submodel:
        raise HTTPException(status_code=400, detail="Missing submodel")
    try:
        response = _basyx_request("POST", "submodels", json_body=payload.submodel)
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}
    created = response.json() if response.content else payload.submodel
    return {"status": "created", "submodel": created}


@router.get("/aas/submodels/{submodel_id}/elements")
def get_submodel_elements(request: Request, submodel_id: str):
    require_roles(
        request.state.user,
        ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"],
    )
    try:
        response = _basyx_request("GET", f"submodels/{submodel_id}/submodel-elements")
    except requests.RequestException as exc:
        return {"error": str(exc), "submodel_id": submodel_id, "items": []}
    payload = response.json() if response.content else {"items": []}
    if isinstance(payload, dict):
        if "submodel_id" not in payload:
            payload["submodel_id"] = submodel_id
        if "items" not in payload:
            payload["items"] = payload.get("submodelElements", [])
        return payload
    return {"submodel_id": submodel_id, "items": payload}


@router.patch("/aas/submodels/{submodel_id}/elements")
def patch_submodel_elements(
    request: Request, submodel_id: str, payload: SubmodelPatchRequest
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    try:
        try:
            response = _basyx_request(
                "PATCH",
                f"submodels/{submodel_id}/submodel-elements",
                json_body=payload.elements,
            )
        except requests.RequestException:
            response = _basyx_request(
                "PUT",
                f"submodels/{submodel_id}/submodel-elements",
                json_body=payload.elements,
            )
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}
    updated = response.json() if response.content else payload.elements
    return {"status": "updated", "submodel_id": submodel_id, "elements": updated}


@router.post("/aasx/upload")
def upload_aasx(request: Request, payload: AasxUploadRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    if not payload.content_base64:
        raise HTTPException(status_code=400, detail="Missing content")
    return {
        "status": "stored",
        "filename": payload.filename,
        "bytes": len(payload.content_base64.encode("utf-8")),
    }
