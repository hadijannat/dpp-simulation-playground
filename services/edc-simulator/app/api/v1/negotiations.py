from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from datetime import datetime, timezone
from ...dsp.negotiation_state_machine import can_transition
from ...store import save_item, load_item
from ...config import REDIS_URL
from redis import Redis
from ...auth import require_roles

router = APIRouter()

class NegotiationCreate(BaseModel):
    consumer_id: str
    provider_id: str
    asset_id: str
    policy: Dict

def _key(neg_id: str) -> str:
    return f"edc:negotiation:{neg_id}"

def _set_state(item: Dict, state: str) -> Dict:
    item["state"] = state
    item.setdefault("state_history", []).append(
        {"state": state, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    return item

@router.post("/negotiations")
def create_negotiation(request: Request, payload: NegotiationCreate):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    neg_id = str(uuid4())
    item = {
        "id": neg_id,
        "state": "INITIAL",
        "policy": payload.policy,
        "asset_id": payload.asset_id,
        "consumer_id": payload.consumer_id,
        "provider_id": payload.provider_id,
        "state_history": [],
    }
    save_item(_key(neg_id), _set_state(item, "INITIAL"))
    return item

@router.get("/negotiations/{negotiation_id}")
def get_negotiation(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    item = load_item(_key(negotiation_id))
    if not item:
        return {"error": "not found"}
    return item

@router.post("/negotiations/{negotiation_id}/accept")
def accept_offer(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "ACCEPTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "ACCEPTED"))
    return item


@router.post("/negotiations/{negotiation_id}/request")
def request_offer(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "REQUESTING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "REQUESTING"))
    return item


@router.post("/negotiations/{negotiation_id}/requested")
def mark_requested(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "REQUESTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "REQUESTED"))
    return item


@router.post("/negotiations/{negotiation_id}/offer")
def offer(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "OFFERED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "OFFERED"))
    return item


@router.post("/negotiations/{negotiation_id}/agree")
def agree(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "AGREED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "AGREED"))
    return item


@router.post("/negotiations/{negotiation_id}/verify")
def verify(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "VERIFIED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "VERIFIED"))
    return item


@router.post("/negotiations/{negotiation_id}/finalize")
def finalize(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "FINALIZED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "FINALIZED"))
    try:
        Redis.from_url(REDIS_URL).xadd(
            "simulation.events",
            {
                "event_type": "edc_negotiation_completed",
                "user_id": request.state.user.get("sub"),
                "negotiation_id": negotiation_id,
            },
        )
    except Exception:
        pass
    return item


@router.post("/negotiations/{negotiation_id}/terminate")
def terminate(request: Request, negotiation_id: str):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = load_item(_key(negotiation_id))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "TERMINATED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    save_item(_key(negotiation_id), _set_state(item, "TERMINATED"))
    return item
