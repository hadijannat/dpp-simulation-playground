from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from ..models.session import SimulationSession


def create_session(db: Session, user_id: str, role: str, state: dict) -> SimulationSession:
    session = SimulationSession(id=uuid4(), user_id=user_id, active_role=role, session_state=state or {})
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> SimulationSession | None:
    return db.query(SimulationSession).filter(SimulationSession.id == session_id).first()


def update_session(
    db: Session,
    session: SimulationSession,
    role: str | None = None,
    state: dict | None = None,
    is_active: bool | None = None,
) -> SimulationSession:
    if role is not None:
        session.active_role = role
    if state is not None:
        session.session_state = state
    if is_active is not None:
        session.is_active = is_active
    session.last_activity = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session
