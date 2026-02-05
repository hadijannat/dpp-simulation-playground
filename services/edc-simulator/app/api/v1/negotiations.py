from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from ...dsp.negotiation_state_machine import can_transition

router = APIRouter()
_store: Dict[str, Dict] = {}

class NegotiationCreate(BaseModel):
    consumer_id: str
    provider_id: str
    asset_id: str
    policy: Dict

@router.post("/negotiations")
def create_negotiation(payload: NegotiationCreate):
    neg_id = str(uuid4())
    _store[neg_id] = {"id": neg_id, "state": "INITIAL", "policy": payload.policy}
    return _store[neg_id]

@router.get("/negotiations/{negotiation_id}")
def get_negotiation(negotiation_id: str):
    return _store.get(negotiation_id, {"error": "not found"})

@router.post("/negotiations/{negotiation_id}/accept")
def accept_offer(negotiation_id: str):
    item = _store.get(negotiation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item["state"], "ACCEPTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    item["state"] = "ACCEPTED"
    return item
