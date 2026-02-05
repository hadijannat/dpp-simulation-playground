from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from ...dsp.transfer_state_machine import can_transition
from ...auth import require_roles

router = APIRouter()
_store: Dict[str, Dict] = {}

class TransferCreate(BaseModel):
    asset_id: str

@router.post("/transfers")
def create_transfer(request: Request, payload: TransferCreate):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    tid = str(uuid4())
    _store[tid] = {"id": tid, "state": "INITIAL", "asset_id": payload.asset_id}
    return _store[tid]

@router.get("/transfers/{transfer_id}")
def get_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    return _store.get(transfer_id, {"error": "not found"})

@router.post("/transfers/{transfer_id}/start")
def start_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = _store.get(transfer_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "PROVISIONING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    item["state"] = "PROVISIONING"
    return item
