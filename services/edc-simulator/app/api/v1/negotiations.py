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
from ...dsp.negotiation_state_machine import can_transition
from ...models.negotiation import EdcNegotiation
from ...odrl.policy_evaluator import evaluate_policy
from services.shared import events
from services.shared.audit import actor_subject, safe_record_audit
from services.shared.redis_client import get_redis, publish_event
from services.shared.user_registry import resolve_user_id
from ...core.webhook_store import record_webhook_event

router = APIRouter()
logger = logging.getLogger(__name__)

NEGOTIATION_ASYNC_FLOW = [
    "REQUESTING",
    "REQUESTED",
    "OFFERED",
    "ACCEPTED",
    "AGREED",
    "VERIFIED",
    "FINALIZED",
]


class NegotiationCreate(BaseModel):
    consumer_id: str
    provider_id: str
    asset_id: str
    policy: dict[str, Any]
    session_id: str | None = None
    purpose: str | None = None
    simulate_async: bool = False
    step_delay_ms: int | None = None
    callback_url: str | None = None
    callback_headers: dict[str, str] | None = None


class NegotiationAction(BaseModel):
    purpose: str | None = None


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


def _set_state(item: EdcNegotiation, state: str) -> None:
    history = item.state_history or []
    history.append({"state": state, "timestamp": datetime.now(timezone.utc).isoformat()})
    item.state_history = history
    item.current_state = state


def _to_dict(item: EdcNegotiation) -> dict[str, Any]:
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


def _publish_state_change_event(
    item: EdcNegotiation,
    *,
    previous_state: str,
    user_id: str | None,
    request_id: str | None,
    async_mode: bool,
) -> None:
    state_event = events.build_event(
        events.EDC_NEGOTIATION_STATE_CHANGED,
        user_id=user_id or "",
        source_service="edc-simulator",
        request_id=request_id,
        session_id=str(item.session_id) if item.session_id else None,
        negotiation_id=item.negotiation_id,
        metadata={
            "previous_state": previous_state,
            "current_state": item.current_state,
            "async_mode": async_mode,
            "asset_id": item.asset_id,
        },
    )
    ok, _ = publish_event(
        get_redis(REDIS_URL),
        "simulation.events",
        state_event,
        maxlen=EVENT_STREAM_MAXLEN,
    )
    if not ok:
        logger.warning(
            "Failed to publish negotiation state change event",
            extra={"negotiation_id": item.negotiation_id, "state": item.current_state},
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
            "Negotiation callback dispatch failed",
            extra={"negotiation_id": payload.get("negotiation_id"), "error": str(exc)},
        )


def _emit_completion_side_effects(
    db: Session,
    *,
    item: EdcNegotiation,
    negotiation_id: str,
    user_id: str | None,
    actor_subject_value: str | None,
    request_id: str | None,
) -> None:
    safe_record_audit(
        db,
        action="edc.negotiation_finalized",
        object_type="edc_negotiation",
        object_id=negotiation_id,
        actor_user_id=user_id,
        actor_subject_value=actor_subject_value,
        session_id=str(item.session_id) if item.session_id else None,
        request_id=request_id,
        details={"state": item.current_state},
    )

    ok, _ = publish_event(
        get_redis(REDIS_URL),
        "simulation.events",
        events.build_event(
            events.EDC_NEGOTIATION_COMPLETED,
            user_id=user_id or "",
            source_service="edc-simulator",
            request_id=request_id,
            negotiation_id=negotiation_id,
            session_id=str(item.session_id) if item.session_id else None,
        ),
        maxlen=EVENT_STREAM_MAXLEN,
    )
    if not ok:
        logger.warning(
            "Failed to publish negotiation completion event",
            extra={"negotiation_id": negotiation_id},
        )


def _run_async_negotiation_flow(
    *,
    negotiation_id: str,
    step_delay_ms: int,
    callback_url: str | None,
    callback_headers: dict[str, str] | None,
    user_id: str | None,
    actor_subject_value: str | None,
    request_id: str | None,
) -> None:
    db = SessionLocal()
    try:
        for target_state in NEGOTIATION_ASYNC_FLOW:
            item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
            if not item:
                return
            if item.current_state in {"TERMINATED", "FINALIZED"}:
                return
            if item.current_state == target_state:
                continue
            if not can_transition(item.current_state, target_state):
                logger.warning(
                    "Skipping invalid async transition",
                    extra={
                        "negotiation_id": negotiation_id,
                        "current_state": item.current_state,
                        "target_state": target_state,
                    },
                )
                continue

            previous_state = item.current_state
            _set_state(item, target_state)
            db.commit()

            _publish_state_change_event(
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
                    "event_type": "negotiation_state_changed",
                    "negotiation_id": negotiation_id,
                    "previous_state": previous_state,
                    "state": item.current_state,
                    "session_id": str(item.session_id) if item.session_id else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "async_mode": True,
                },
            )

            if target_state == "FINALIZED":
                _emit_completion_side_effects(
                    db,
                    item=item,
                    negotiation_id=negotiation_id,
                    user_id=user_id,
                    actor_subject_value=actor_subject_value,
                    request_id=request_id,
                )
                return

            if step_delay_ms > 0:
                time.sleep(step_delay_ms / 1000.0)
    except Exception:
        logger.exception("Async negotiation simulation failed", extra={"negotiation_id": negotiation_id})
    finally:
        db.close()


@router.post("/negotiations")
def create_negotiation(
    request: Request,
    payload: NegotiationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    neg_id = str(uuid4())
    item = EdcNegotiation(
        id=uuid4(),
        negotiation_id=neg_id,
        consumer_participant_id=payload.consumer_id,
        provider_participant_id=payload.provider_id,
        asset_id=payload.asset_id,
        policy_odrl=payload.policy,
        session_id=_safe_uuid(payload.session_id),
    )
    _set_state(item, "INITIAL")
    db.add(item)
    db.commit()
    db.refresh(item)

    if payload.simulate_async:
        user_id = resolve_user_id(db, request.state.user)
        background_tasks.add_task(
            _run_async_negotiation_flow,
            negotiation_id=neg_id,
            step_delay_ms=_resolved_step_delay_ms(payload.step_delay_ms),
            callback_url=payload.callback_url,
            callback_headers=payload.callback_headers,
            user_id=user_id,
            actor_subject_value=actor_subject(getattr(request.state, "user", None)),
            request_id=str(getattr(request.state, "request_id", "")) or None,
        )

    return _to_dict(item)


@router.get("/negotiations/{negotiation_id}")
def get_negotiation(request: Request, negotiation_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_dict(item)


@router.post("/negotiations/{negotiation_id}/simulate")
def simulate_negotiation(
    request: Request,
    negotiation_id: str,
    payload: AsyncSimulationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcNegotiation).filter(EdcNegotiation.negotiation_id == negotiation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    if item.current_state in {"FINALIZED", "TERMINATED"}:
        return _to_dict(item)

    user_id = resolve_user_id(db, request.state.user)
    background_tasks.add_task(
        _run_async_negotiation_flow,
        negotiation_id=negotiation_id,
        step_delay_ms=_resolved_step_delay_ms(payload.step_delay_ms),
        callback_url=payload.callback_url,
        callback_headers=payload.callback_headers,
        user_id=user_id,
        actor_subject_value=actor_subject(getattr(request.state, "user", None)),
        request_id=str(getattr(request.state, "request_id", "")) or None,
    )
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
    previous_state = item.current_state
    _set_state(item, "FINALIZED")
    db.commit()

    user_id = resolve_user_id(db, request.state.user)
    _publish_state_change_event(
        item,
        previous_state=previous_state,
        user_id=user_id,
        request_id=str(getattr(request.state, "request_id", "")) or None,
        async_mode=False,
    )
    _emit_completion_side_effects(
        db,
        item=item,
        negotiation_id=negotiation_id,
        user_id=user_id,
        actor_subject_value=actor_subject(getattr(request.state, "user", None)),
        request_id=str(getattr(request.state, "request_id", "")) or None,
    )
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
