from typing import Dict, Any

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...config import BASYX_BASE_URL, BASYX_API_PREFIX

router = APIRouter()


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
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    try:
        response = requests.get(f"{BASYX_BASE_URL}{BASYX_API_PREFIX}", timeout=8)
        response.raise_for_status()
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
        response = requests.post(f"{BASYX_BASE_URL}{BASYX_API_PREFIX}", json=shell, timeout=8)
        response.raise_for_status()
        return {"status": "created", "shell": response.json()}
    except requests.RequestException as exc:
        return {"status": "degraded", "shell": shell, "error": str(exc)}


@router.post("/aas/submodels")
def create_submodel(request: Request, payload: SubmodelCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    if not payload.submodel:
        raise HTTPException(status_code=400, detail="Missing submodel")
    return {"status": "created", "submodel": payload.submodel}


@router.patch("/aas/submodels/{submodel_id}/elements")
def patch_submodel_elements(request: Request, submodel_id: str, payload: SubmodelPatchRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return {"status": "updated", "submodel_id": submodel_id, "elements": payload.elements}


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
