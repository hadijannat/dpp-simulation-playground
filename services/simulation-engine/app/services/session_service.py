from sqlalchemy.orm import Session
from ..repositories.session_repo import create_session, get_session, update_session


def create_new_session(db: Session, user_id: str, role: str, state: dict):
    return create_session(db, user_id, role, state)


def fetch_session(db: Session, session_id: str):
    return get_session(db, session_id)


def update_existing_session(db: Session, session, role=None, state=None, is_active=None):
    return update_session(db, session, role=role, state=state, is_active=is_active)
