from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import AAS_ADAPTER_URL
from ...core.proxy import request_json
from ...schemas.v2 import (
    AasCreateRequest,
    AasShellCreateResponse,
    AasShellListResponse,
    AasSubmodelCreateRequest,
    AasSubmodelCreateResponse,
    AasSubmodelPatchRequest,
    AasSubmodelPatchResponse,
    AasxUploadRequest,
    AasxUploadResponse,
)

router = APIRouter()


@router.get("/aas/shells", response_model=AasShellListResponse)
def list_shells(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{AAS_ADAPTER_URL}/api/v2/aas/shells")
    return {"items": payload.get("items", [])}


@router.post("/aas/shells", response_model=AasShellCreateResponse)
def create_shell(request: Request, payload: AasCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    adapter_payload = {
        "aas_identifier": payload.aas_identifier,
        "product_name": payload.product_name,
        "product_identifier": payload.product_identifier,
    }
    response = request_json(
        request,
        "POST",
        f"{AAS_ADAPTER_URL}/api/v2/aas/shells",
        json_body=adapter_payload,
    )
    return {
        "status": response.get("status", "unknown"),
        "shell": response.get("shell") or response.get("aas"),
        "error": response.get("error"),
    }


@router.post("/aas/submodels", response_model=AasSubmodelCreateResponse)
def create_submodel(request: Request, payload: AasSubmodelCreateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    response = request_json(
        request,
        "POST",
        f"{AAS_ADAPTER_URL}/api/v2/aas/submodels",
        json_body=payload.model_dump(),
    )
    return {
        "status": response.get("status", "unknown"),
        "submodel": response.get("submodel"),
        "error": response.get("error"),
    }


@router.patch("/aas/submodels/{submodel_id}/elements", response_model=AasSubmodelPatchResponse)
def patch_submodel_elements(request: Request, submodel_id: str, payload: AasSubmodelPatchRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    response = request_json(
        request,
        "PATCH",
        f"{AAS_ADAPTER_URL}/api/v2/aas/submodels/{submodel_id}/elements",
        json_body=payload.model_dump(),
    )
    return {
        "status": response.get("status", "unknown"),
        "submodel_id": response.get("submodel_id") or submodel_id,
        "elements": response.get("elements", payload.elements),
        "error": response.get("error"),
    }


@router.post("/aasx/upload", response_model=AasxUploadResponse)
def upload_aasx(request: Request, payload: AasxUploadRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    response = request_json(
        request,
        "POST",
        f"{AAS_ADAPTER_URL}/api/v2/aasx/upload",
        json_body=payload.model_dump(),
    )
    return {
        "status": response.get("status", "unknown"),
        "filename": response.get("filename") or payload.filename,
        "bytes": response.get("bytes"),
        "storage": response.get("storage"),
    }
