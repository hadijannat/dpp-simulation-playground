from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
from ...dsp.transfer_state_machine import can_transition
from ...store import save_item, load_item
from ...auth import require_roles

router = APIRouter()

class TransferCreate(BaseModel):
    asset_id: str

def _key(transfer_id: str) -> str:
    return f\"edc:transfer:{transfer_id}\"

def _set_state(item: dict, state: str) -> dict:
    item[\"state\"] = state
    item.setdefault(\"state_history\", []).append(
        {\"state\": state, \"timestamp\": datetime.now(timezone.utc).isoformat()}
    )
    return item

@router.post("/transfers")
def create_transfer(request: Request, payload: TransferCreate):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    tid = str(uuid4())
    item = {"id": tid, "state": "INITIAL", "asset_id": payload.asset_id, "state_history": []}
    save_item(_key(tid), _set_state(item, "INITIAL"))
    return item

@router.get("/transfers/{transfer_id}")
def get_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    item = load_item(_key(transfer_id))
    if not item:
        return {"error": "not found"}
    return item

@router.post("/transfers/{transfer_id}/provision")
def provision_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "PROVISIONING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "PROVISIONING"))
    return item


@router.post("/transfers/{transfer_id}/provisioned")
def provisioned(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "PROVISIONED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "PROVISIONED"))
    return item


@router.post("/transfers/{transfer_id}/request")
def request_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "REQUESTING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "REQUESTING"))
    return item


@router.post("/transfers/{transfer_id}/requested")
def requested(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "REQUESTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "REQUESTED"))
    return item


@router.post("/transfers/{transfer_id}/start")
def start_transfer(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "STARTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "STARTED"))
    return item


@router.post("/transfers/{transfer_id}/complete")
def complete(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "COMPLETED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "COMPLETED"))
    return item


@router.post("/transfers/{transfer_id}/terminate")
def terminate(request: Request, transfer_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(transfer_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "TERMINATED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(transfer_id), _set_state(item, "TERMINATED"))
    return item
