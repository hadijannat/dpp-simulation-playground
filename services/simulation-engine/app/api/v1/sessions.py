from fastapi import APIRouter, HTTPException
from ..schemas.session_schema import SessionCreate, SessionResponse
from ...core.db import SessionLocal
from ...services.session_service import create_new_session, fetch_session

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse)
def create_session(payload: SessionCreate):
    db = SessionLocal()
    session = create_new_session(db, payload.user_id, payload.role, payload.state or {})
    return SessionResponse(id=str(session.id), user_id=str(session.user_id), role=session.active_role, state=session.session_state)

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    db = SessionLocal()
    session = fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": str(session.id), "user_id": str(session.user_id), "role": session.active_role, "state": session.session_state}
