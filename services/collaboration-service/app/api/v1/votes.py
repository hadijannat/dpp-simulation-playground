from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
import logging
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.vote import Vote
from ...models.annotation import Annotation
from ...models.gap_report import GapReport
from ...config import REDIS_URL, EVENT_STREAM_MAXLEN
from ...auth import require_roles
from services.shared import events
from services.shared.outbox import emit_event
from services.shared.user_registry import resolve_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


class VoteCreate(BaseModel):
    target_id: str
    value: int


@router.get("/votes")
def list_votes(
    request: Request,
    target_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(
        request.state.user, ["developer", "admin", "regulator", "manufacturer"]
    )
    query = db.query(Vote)
    if target_id:
        query = query.filter(Vote.target_id == target_id)
    items = query.order_by(Vote.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {"id": str(item.id), "target_id": item.target_id, "value": item.value}
            for item in items
        ]
    }


@router.post("/votes")
def create_vote(request: Request, payload: VoteCreate, db: Session = Depends(get_db)):
    require_roles(
        request.state.user,
        ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"],
    )
    raw_user_id = resolve_user_id(db, request.state.user)
    if not raw_user_id:
        raise HTTPException(status_code=400, detail="Missing user id")
    try:
        user_id = UUID(str(raw_user_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc
    existing = (
        db.query(Vote)
        .filter(Vote.user_id == user_id, Vote.target_id == payload.target_id)
        .first()
    )
    if existing:
        return {
            "id": str(existing.id),
            "target_id": existing.target_id,
            "value": existing.value,
        }
    item = Vote(
        id=uuid4(), user_id=user_id, target_id=payload.target_id, value=payload.value
    )
    db.add(item)
    target_type = "unknown"
    target_uuid: UUID | None = None
    try:
        target_uuid = UUID(payload.target_id)
    except ValueError:
        target_uuid = None

    annotation = (
        db.query(Annotation).filter(Annotation.id == target_uuid).first()
        if target_uuid
        else None
    )
    if annotation:
        annotation.votes_count = (annotation.votes_count or 0) + payload.value
        target_type = "annotation"
    gap_report = (
        db.query(GapReport).filter(GapReport.id == target_uuid).first()
        if target_uuid
        else None
    )
    if gap_report:
        gap_report.votes_count = (gap_report.votes_count or 0) + payload.value
        target_type = "gap_report"
    db.commit()
    try:
        ok, _ = emit_event(
            db,
            stream="simulation.events",
            payload=events.build_event(
                events.VOTE_CAST,
                user_id=str(user_id),
                source_service="collaboration-service",
                request_id=getattr(request.state, "request_id", None),
                metadata={
                    "vote_id": str(item.id),
                    "target_id": payload.target_id,
                    "target_type": target_type,
                    "value": payload.value,
                },
            ),
            redis_url=REDIS_URL,
            maxlen=EVENT_STREAM_MAXLEN,
            commit=True,
            log=logger,
        )
        if not ok:
            logger.warning(
                "Failed to publish vote_cast event", extra={"vote_id": str(item.id)}
            )
    except Exception as exc:
        logger.warning(
            "Error while publishing vote_cast event",
            extra={"vote_id": str(item.id), "error": str(exc)},
        )
    return {"id": str(item.id), "target_id": item.target_id, "value": item.value}
