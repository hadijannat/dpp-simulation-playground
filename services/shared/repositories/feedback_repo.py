from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.ux_feedback import UxFeedback


def create_feedback(
    db: Session,
    user_id,
    journey_run_id=None,
    locale: str = "en",
    role: str = "manufacturer",
    flow: str = "manufacturer-core-e2e",
    score: int = 5,
    comment: str | None = None,
) -> UxFeedback:
    feedback = UxFeedback(
        id=uuid4(),
        user_id=user_id,
        journey_run_id=journey_run_id,
        locale=locale,
        role=role,
        flow=flow,
        score=score,
        comment=comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def list_feedback(db: Session, flow: str | None = None, limit: int = 50) -> list[UxFeedback]:
    query = db.query(UxFeedback)
    if flow:
        query = query.filter(UxFeedback.flow == flow)
    return query.order_by(UxFeedback.created_at.desc()).limit(limit).all()
