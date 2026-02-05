from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from ...schemas.session_schema import SessionCreate, SessionResponse, SessionUpdate
from ...core.db import get_db
from ...services.session_service import create_new_session, fetch_session, update_existing_session
from ...auth import require_roles
from services.shared.user_registry import resolve_user_id

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse)
def create_session(request: Request, payload: SessionCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    user_id = resolve_user_id(db, request.state.user)
    if not user_id and payload.user_id:
        try:
            user_id = str(UUID(payload.user_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user id")
    session = create_new_session(db, user_id, payload.role, payload.state or {})
    return SessionResponse(id=str(session.id), user_id=str(session.user_id), role=session.active_role, state=session.session_state)

@router.get("/sessions/{session_id}")
def get_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": str(session.id), "user_id": str(session.user_id), "role": session.active_role, "state": session.session_state}


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(request: Request, session_id: str, payload: SessionUpdate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = update_existing_session(db, session, role=payload.role, state=payload.state, is_active=payload.is_active)
    return SessionResponse(id=str(updated.id), user_id=str(updated.user_id), role=updated.active_role, state=updated.session_state)


@router.delete("/sessions/{session_id}")
def close_session(request: Request, session_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_existing_session(db, session, is_active=False)
    return {"status": "closed", "id": str(session.id)}
