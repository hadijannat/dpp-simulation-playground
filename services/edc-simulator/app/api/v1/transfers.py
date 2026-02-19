from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Any
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...config import (
    ASYNC_SIMULATION_CALLBACK_TIMEOUT_SECONDS,
    ASYNC_SIMULATION_DEFAULT_STEP_DELAY_MS,
    EVENT_STREAM_MAXLEN,
    REDIS_URL,
)
from ...core.db import SessionLocal, get_db
from ...dsp.transfer_state_machine import can_transition
from ...models.transfer import EdcTransfer
from ...core.webhook_store import record_webhook_event
from services.shared import events
from services.shared.audit import actor_subject, safe_record_audit
from services.shared.outbox import emit_event
from services.shared.user_registry import resolve_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

TRANSFER_ASYNC_FLOW = [
    "PROVISIONING",
    "PROVISIONED",
    "REQUESTING",
    "REQUESTED",
    "STARTED",
    "COMPLETED",
]


class TransferCreate(BaseModel):
    asset_id: str
    session_id: str | None = None
    consumer_id: str | None = None
    provider_id: str | None = None
    simulate_async: bool = False
    step_delay_ms: int | None = None
    callback_url: str | None = None
    callback_headers: dict[str, str] | None = None


class AsyncSimulationRequest(BaseModel):
    step_delay_ms: int | None = None
    callback_url: str | None = None
    callback_headers: dict[str, str] | None = None


def _safe_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _resolved_step_delay_ms(value: int | None) -> int:
    if value is None:
        return ASYNC_SIMULATION_DEFAULT_STEP_DELAY_MS
    if value < 0:
        return 0
    return min(value, 60_000)


def _set_state(item: EdcTransfer, state: str) -> None:
    history = item.state_history or []
    history.append(
        {"state": state, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    item.state_history = history
    item.current_state = state


def _to_dict(item: EdcTransfer) -> dict[str, Any]:
    return {
        "id": str(item.transfer_id),
        "state": item.current_state,
        "asset_id": item.asset_id,
        "consumer_id": item.consumer_participant_id,
        "provider_id": item.provider_participant_id,
        "state_history": item.state_history or [],
        "session_id": str(item.session_id) if item.session_id else None,
    }


def _publish_state_change_event(
    db: Session,
    item: EdcTransfer,
    *,
    previous_state: str,
    user_id: str | None,
    request_id: str | None,
    async_mode: bool,
) -> None:
    state_event = events.build_event(
        events.EDC_TRANSFER_STATE_CHANGED,
        user_id=user_id or "",
        source_service="edc-simulator",
        request_id=request_id,
        session_id=str(item.session_id) if item.session_id else None,
        transfer_id=item.transfer_id,
        metadata={
            "previous_state": previous_state,
            "current_state": item.current_state,
            "async_mode": async_mode,
            "asset_id": item.asset_id,
        },
    )
    ok, _ = emit_event(
        db,
        stream="simulation.events",
        payload=state_event,
        redis_url=REDIS_URL,
        maxlen=EVENT_STREAM_MAXLEN,
        commit=True,
        log=logger,
    )
    if not ok:
        logger.warning(
            "Failed to publish transfer state change event",
            extra={"transfer_id": item.transfer_id, "state": item.current_state},
        )


def _send_callback(
    *,
    callback_url: str | None,
    callback_headers: dict[str, str] | None,
    payload: dict[str, Any],
) -> None:
    if not callback_url:
        return
    try:
        response = requests.post(
            callback_url,
            json=payload,
            headers=callback_headers or {},
            timeout=ASYNC_SIMULATION_CALLBACK_TIMEOUT_SECONDS,
        )
        record_webhook_event(
            channel="outbound",
            callback_url=callback_url,
            status_code=response.status_code,
            payload=payload,
        )
    except Exception as exc:
        record_webhook_event(
            channel="outbound",
            callback_url=callback_url,
            error=str(exc),
            payload=payload,
        )
        logger.warning(
            "Transfer callback dispatch failed",
            extra={"transfer_id": payload.get("transfer_id"), "error": str(exc)},
        )


def _emit_completion_side_effects(
    db: Session,
    *,
    item: EdcTransfer,
    transfer_id: str,
    user_id: str | None,
    actor_subject_value: str | None,
    request_id: str | None,
) -> None:
    safe_record_audit(
        db,
        action="edc.transfer_completed",
        object_type="edc_transfer",
        object_id=transfer_id,
        actor_user_id=user_id,
        actor_subject_value=actor_subject_value,
        session_id=str(item.session_id) if item.session_id else None,
        request_id=request_id,
        details={"state": item.current_state},
    )

    ok, _ = emit_event(
        db,
        stream="simulation.events",
        payload=events.build_event(
            events.EDC_TRANSFER_COMPLETED,
            user_id=user_id or "",
            source_service="edc-simulator",
            request_id=request_id,
            transfer_id=transfer_id,
            session_id=str(item.session_id) if item.session_id else None,
        ),
        redis_url=REDIS_URL,
        maxlen=EVENT_STREAM_MAXLEN,
        commit=True,
        log=logger,
    )
    if not ok:
        logger.warning(
            "Failed to publish transfer completion event",
            extra={"transfer_id": transfer_id},
        )


def _run_async_transfer_flow(
    *,
    transfer_id: str,
    step_delay_ms: int,
    callback_url: str | None,
    callback_headers: dict[str, str] | None,
    user_id: str | None,
    actor_subject_value: str | None,
    request_id: str | None,
) -> None:
    db = SessionLocal()
    try:
        for target_state in TRANSFER_ASYNC_FLOW:
            item = (
                db.query(EdcTransfer)
                .filter(EdcTransfer.transfer_id == transfer_id)
                .first()
            )
            if not item:
                return
            if item.current_state in {"TERMINATED", "COMPLETED"}:
                return
            if item.current_state == target_state:
                continue
            if not can_transition(item.current_state, target_state):
                logger.warning(
                    "Skipping invalid async transfer transition",
                    extra={
                        "transfer_id": transfer_id,
                        "current_state": item.current_state,
                        "target_state": target_state,
                    },
                )
                continue

            previous_state = item.current_state
            _set_state(item, target_state)
            db.commit()

            _publish_state_change_event(
                db,
                item,
                previous_state=previous_state,
                user_id=user_id,
                request_id=request_id,
                async_mode=True,
            )
            _send_callback(
                callback_url=callback_url,
                callback_headers=callback_headers,
                payload={
                    "event_type": "transfer_state_changed",
                    "transfer_id": transfer_id,
                    "previous_state": previous_state,
                    "state": item.current_state,
                    "session_id": str(item.session_id) if item.session_id else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "async_mode": True,
                },
            )

            if target_state == "COMPLETED":
                _emit_completion_side_effects(
                    db,
                    item=item,
                    transfer_id=transfer_id,
                    user_id=user_id,
                    actor_subject_value=actor_subject_value,
                    request_id=request_id,
                )
                return

            if step_delay_ms > 0:
                time.sleep(step_delay_ms / 1000.0)
    except Exception:
        logger.exception(
            "Async transfer simulation failed", extra={"transfer_id": transfer_id}
        )
    finally:
        db.close()


@router.post("/transfers")
def create_transfer(
    request: Request,
    payload: TransferCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    tid = str(uuid4())
    item = EdcTransfer(
        id=uuid4(),
        transfer_id=tid,
        asset_id=payload.asset_id,
        session_id=_safe_uuid(payload.session_id),
        consumer_participant_id=payload.consumer_id,
        provider_participant_id=payload.provider_id,
    )
    _set_state(item, "INITIAL")
    db.add(item)
    db.commit()
    db.refresh(item)

    if payload.simulate_async:
        user_id = resolve_user_id(db, request.state.user)
        background_tasks.add_task(
            _run_async_transfer_flow,
            transfer_id=tid,
            step_delay_ms=_resolved_step_delay_ms(payload.step_delay_ms),
            callback_url=payload.callback_url,
            callback_headers=payload.callback_headers,
            user_id=user_id,
            actor_subject_value=actor_subject(getattr(request.state, "user", None)),
            request_id=str(getattr(request.state, "request_id", "")) or None,
        )

    return _to_dict(item)


@router.get("/transfers/{transfer_id}")
def get_transfer(request: Request, transfer_id: str, db: Session = Depends(get_db)):
    require_roles(
        request.state.user, ["developer", "manufacturer", "admin", "regulator"]
    )
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/simulate")
def simulate_transfer(
    request: Request,
    transfer_id: str,
    payload: AsyncSimulationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcTransfer).filter(EdcTransfer.transfer_id == transfer_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    if item.current_state in {"COMPLETED", "TERMINATED"}:
        return _to_dict(item)

    user_id = resolve_user_id(db, request.state.user)
    background_tasks.add_task(
        _run_async_transfer_flow,
        transfer_id=transfer_id,
        step_delay_ms=_resolved_step_delay_ms(payload.step_delay_ms),
        callback_url=payload.callback_url,
        callback_headers=payload.callback_headers,
        user_id=user_id,
        actor_subject_value=actor_subject(getattr(request.state, "user", None)),
        request_id=str(getattr(request.state, "request_id", "")) or None,
    )
    return _to_dict(item)


@router.post("/transfers/{transfer_id}/provision")
def provision_transfer(
    request: Request, transfer_id: str, db: Session = Depends(get_db)
):
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

    previous_state = item.current_state
    _set_state(item, "COMPLETED")
    db.commit()

    user_id = resolve_user_id(db, request.state.user)
    _publish_state_change_event(
        db,
        item,
        previous_state=previous_state,
        user_id=user_id,
        request_id=str(getattr(request.state, "request_id", "")) or None,
        async_mode=False,
    )
    _emit_completion_side_effects(
        db,
        item=item,
        transfer_id=transfer_id,
        user_id=user_id,
        actor_subject_value=actor_subject(getattr(request.state, "user", None)),
        request_id=str(getattr(request.state, "request_id", "")) or None,
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
