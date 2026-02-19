from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from ...dsp.transfer_state_machine import can_transition
from ...auth import require_roles
from ...core.db import get_db
from ...models.transfer import EdcTransfer
from ...config import REDIS_URL, EVENT_STREAM_MAXLEN
from services.shared.user_registry import resolve_user_id
from services.shared import events
from services.shared.redis_client import get_redis, publish_event

router = APIRouter()
logger = logging.getLogger(__name__)


class TransferCreate(BaseModel):
    asset_id: str
    session_id: str | None = None
    consumer_id: str | None = None
    provider_id: str | None = None


def _set_state(item: EdcTransfer, state: str) -> None:
    history = item.state_history or []
    history.append({"state": state, "timestamp": datetime.now(timezone.utc).isoformat()})
    item.state_history = history
    item.current_state = state


def _to_dict(item: EdcTransfer) -> dict:
    return {
        "id": str(item.transfer_id),
        "state": item.current_state,
        "asset_id": item.asset_id,
        "consumer_id": item.consumer_participant_id,
        "provider_id": item.provider_participant_id,
        "state_history": item.state_history or [],
        "session_id": str(item.session_id) if item.session_id else None,
    }


@router.post("/transfers")
def create_transfer(request: Request, payload: TransferCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    tid = str(uuid4())
    item = EdcTransfer(
        id=uuid4(),
        transfer_id=tid,
        asset_id=payload.asset_id,
        session_id=payload.session_id,
        consumer_participant_id=payload.consumer_id,
        provider_participant_id=payload.provider_id,
    )
    _set_state(item, "INITIAL")
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_dict(item)


@router.get("/transfers/{transfer_id}")
def get_transfer(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/provision")
def provision_transfer(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "PROVISIONING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "PROVISIONING")
    db.commit()
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/provisioned")
def provisioned(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "PROVISIONED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "PROVISIONED")
    db.commit()
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/request")
def request_transfer(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "REQUESTING"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "REQUESTING")
    db.commit()
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/requested")
def requested(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "REQUESTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "REQUESTED")
    db.commit()
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/start")
def start_transfer(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "STARTED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "STARTED")
    db.commit()
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/complete")
def complete(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "COMPLETED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "COMPLETED")
    db.commit()
    try:
        user_id = resolve_user_id(db, request.state.user)
        ok, _ = publish_event(
            get_redis(REDIS_URL),
            "simulation.events",
            events.build_event(
                events.EDC_TRANSFER_COMPLETED,
                user_id=user_id or "",
                source_service="edc-simulator",
                request_id=getattr(request.state, "request_id", None),
                transfer_id=transfer_id,
                session_id=str(item.session_id) if item.session_id else None,
            ),
            maxlen=EVENT_STREAM_MAXLEN,
        )
        if not ok:
            logger.warning("Failed to publish transfer completion event", extra={"transfer_id": transfer_id})
    except Exception as exc:
        logger.warning(
            "Error while publishing transfer completion event",
            extra={"transfer_id": transfer_id, "error": str(exc)},
        )
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/terminate")
def terminate(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_transition(item.current_state, "TERMINATED"):
        raise HTTPException(status_code=400, detail="Invalid transition")
    _set_state(item, "TERMINATED")
    db.commit()
    return _to_dict(item)
