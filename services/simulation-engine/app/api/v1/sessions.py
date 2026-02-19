from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from ...core.session_state import (
    assert_transition_allowed,
    get_lifecycle_state,
    set_lifecycle_state,
)
from ...schemas.session_schema import SessionCreate, SessionResponse, SessionUpdate
from ...services.session_service import create_new_session, fetch_session, update_existing_session
from services.shared.user_registry import resolve_user_id

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


def _to_session_response(session) -> SessionResponse:
    lifecycle_state = get_lifecycle_state(session.session_state, is_active=bool(session.is_active))
    return SessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        role=session.active_role,
        state=session.session_state or {},
        lifecycle_state=lifecycle_state,
        is_active=bool(session.is_active),
    )


def _transition_session_state(session, *, target_state: str) -> None:
    current = get_lifecycle_state(session.session_state, is_active=bool(session.is_active))
    assert_transition_allowed(current, target_state)
    session.session_state = set_lifecycle_state(session.session_state, target_state)
    session.is_active = target_state == "active"
    session.last_activity = datetime.now(timezone.utc)


@router.post("/sessions", response_model=SessionResponse)
def create_session(request: Request, payload: SessionCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    user_id = resolve_user_id(db, request.state.user)
    if not user_id and payload.user_id:
        try:
            user_id = str(UUID(payload.user_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid user id") from exc
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user id")

    initial_state = payload.state or {}
    lifecycle_state = payload.lifecycle_state or "active"
    try:
        initial_state = set_lifecycle_state(initial_state, lifecycle_state)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session = create_new_session(db, user_id, payload.role, initial_state)
    if lifecycle_state != "active":
        session.is_active = False
        session.last_activity = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return _to_session_response(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_session_response(session)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(request: Request, session_id: str, payload: SessionUpdate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    next_state = payload.state
    is_active = payload.is_active
    if payload.lifecycle_state is not None:
        current = get_lifecycle_state(session.session_state, is_active=bool(session.is_active))
        assert_transition_allowed(current, payload.lifecycle_state)
        merged_state = dict(session.session_state or {})
        if next_state:
            merged_state.update(next_state)
        next_state = set_lifecycle_state(merged_state, payload.lifecycle_state)
        is_active = payload.lifecycle_state == "active"

    updated = update_existing_session(db, session, role=payload.role, state=next_state, is_active=is_active)
    return _to_session_response(updated)


@router.post("/sessions/{session_id}/pause", response_model=SessionResponse)
def pause_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _transition_session_state(session, target_state="paused")
    db.commit()
    db.refresh(session)
    return _to_session_response(session)


@router.post("/sessions/{session_id}/resume", response_model=SessionResponse)
def resume_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _transition_session_state(session, target_state="active")
    db.commit()
    db.refresh(session)
    return _to_session_response(session)


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
def complete_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _transition_session_state(session, target_state="completed")
    db.commit()
    db.refresh(session)
    return _to_session_response(session)


@router.delete("/sessions/{session_id}")
def close_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    current = get_lifecycle_state(session.session_state, is_active=bool(session.is_active))
    if current not in {"completed", "failed"}:
        session.session_state = set_lifecycle_state(session.session_state, "completed")
    session.is_active = False
    session.last_activity = datetime.now(timezone.utc)
    db.commit()
    return {"status": "closed", "id": str(session.id)}
