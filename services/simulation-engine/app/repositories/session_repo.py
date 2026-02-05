from sqlalchemy.orm import Session
from uuid import uuid4
from ..models.session import SimulationSession


def create_session(db: Session, user_id: str, role: str, state: dict) -> SimulationSession:
    session = SimulationSession(id=uuid4(), user_id=user_id, active_role=role, session_state=state or {})
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> SimulationSession | None:
    return db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
