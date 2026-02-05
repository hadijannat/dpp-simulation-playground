from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from redis import Redis

from ...dsp.negotiation_state_machine import can_transition
from ...auth import require_roles
from ...core.db import get_db
from ...models.negotiation import EdcNegotiation
from ...config import REDIS_URL
from ...odrl.policy_evaluator import evaluate_policy
from services.shared.user_registry import resolve_user_id
from services.shared import events

router = APIRouter()


class NegotiationCreate(BaseModel):
    consumer_id: str
    provider_id: str
    asset_id: str
    policy: Dict
    session_id: str | None = None
    purpose: str | None = None


class NegotiationAction(BaseModel):
    purpose: str | None = None


def _set_state(item: EdcNegotiation, state: str) -> None:
    history = item.state_history or []
    history.append({"state": state, "timestamp": datetime.now(timezone.utc).isoformat()})
    item.state_history = history
    item.current_state = state


def _to_dict(item: EdcNegotiation) -> dict:
    return {
        "id": str(item.negotiation_id),
        "state": item.current_state,
        "policy": item.policy_odrl or {},
        "asset_id": item.asset_id,
        "consumer_id": item.consumer_participant_id,
        "provider_id": item.provider_participant_id,
        "state_history": item.state_history or [],
        "session_id": str(item.session_id) if item.session_id else None,
    }


def _enforce_policy(item: EdcNegotiation, payload: NegotiationAction | None) -> None:
    if not payload or not payload.purpose:
        return
    allowed = evaluate_policy(item.policy_odrl or {}, payload.purpose)
    if not allowed:
        raise HTTPException(status_code=403, detail="Policy does not allow this purpose")


@router.post("/negotiations")
def create_negotiation(request: Request, payload: NegotiationCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    neg_id = str(uuid4())
    item = EdcNegotiation(
        id=uuid4(),
        negotiation_id=neg_id,
        consumer_participant_id=payload.consumer_id,
        provider_participant_id=payload.provider_id,
        asset_id=payload.asset_id,
        policy_odrl=payload.policy,
        session_id=payload.session_id,
    )
    _set_state(item, "INITIAL")
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_dict(item)


@router.get("/negotiations/{negotiation_id}")
def get_negotiation(request: Request, negotiation_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        return {"error": "not found"}
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/accept")
def accept_offer(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "ACCEPTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "ACCEPTED")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/request")
def request_offer(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "REQUESTING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "REQUESTING")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/requested")
def mark_requested(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "REQUESTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "REQUESTED")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/offer")
def offer(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "OFFERED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "OFFERED")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/agree")
def agree(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "AGREED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "AGREED")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/verify")
def verify(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "VERIFIED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "VERIFIED")
    db.commit()
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/finalize")
def finalize(
    request: Request,
    negotiation_id: str,
    payload: NegotiationAction | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "FINALIZED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _enforce_policy(item, payload)
    _set_state(item, "FINALIZED")
    db.commit()
    try:
        user_id = resolve_user_id(db, request.state.user)
        Redis.from_url(REDIS_URL).xadd(
            "simulation.events",
            events.build_event(
                events.EDC_NEGOTIATION_COMPLETED,
                user_id=user_id or "",
                negotiation_id=negotiation_id,
                session_id=str(item.session_id) if item.session_id else None,
            ),
        )
    except Exception:
        pass
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/terminate")
def terminate(request: Request, negotiation_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "TERMINATED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "TERMINATED")
    db.commit()
    return _to_dict(item)
