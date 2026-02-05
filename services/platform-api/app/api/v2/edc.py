from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import EDC_URL
from ...core.proxy import request_json
from ...schemas.v2 import (
    AssetListResponse,
    CatalogResponse,
    NegotiationCreate,
    NegotiationResponse,
    ParticipantListResponse,
    TransferCreate,
    TransferResponse,
)

router = APIRouter()


@router.get("/edc/catalog", response_model=CatalogResponse)
def get_catalog(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{EDC_URL}/api/v1/edc/catalog")
    return {"dataset": payload.get("dataset", [])}


@router.get("/edc/participants", response_model=ParticipantListResponse)
def get_participants(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{EDC_URL}/api/v1/edc/participants")
    return {"items": payload.get("items", [])}


@router.get("/edc/assets", response_model=AssetListResponse)
def get_assets(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{EDC_URL}/api/v1/edc/assets")
    return {"items": payload.get("items", [])}


@router.post("/edc/negotiations", response_model=NegotiationResponse)
def create_negotiation(request: Request, payload: NegotiationCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/negotiations",
        json_body=payload.model_dump(),
    )


@router.post("/edc/negotiations/{negotiation_id}/actions/{action}", response_model=NegotiationResponse)
def run_negotiation_action(request: Request, negotiation_id: str, action: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/negotiations/{negotiation_id}/{action}",
        json_body={},
    )


@router.post("/edc/transfers", response_model=TransferResponse)
def create_transfer(request: Request, payload: TransferCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/transfers",
        json_body=payload.model_dump(),
    )


@router.post("/edc/transfers/{transfer_id}/actions/{action}", response_model=TransferResponse)
def run_transfer_action(request: Request, transfer_id: str, action: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return request_json(
        request,
        "POST",
        f"{EDC_URL}/api/v1/edc/transfers/{transfer_id}/{action}",
        json_body={},
    )
