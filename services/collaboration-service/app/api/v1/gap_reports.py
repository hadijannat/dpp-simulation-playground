from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import logging
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.gap_report import GapReport
from ...config import REDIS_URL, EVENT_STREAM_MAXLEN
from ...auth import require_roles
from services.shared.audit import actor_subject, safe_record_audit
from services.shared.user_registry import resolve_user_id
from services.shared import events
from services.shared.redis_client import get_redis, publish_event

router = APIRouter()
logger = logging.getLogger(__name__)

class GapReportCreate(BaseModel):
    story_id: int | None = None
    description: str


class GapReportUpdate(BaseModel):
    status: str | None = None
    description: str | None = None

@router.get("/gap_reports")
def list_reports(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(GapReport)
    if story_id is not None:
        query = query.filter(GapReport.story_id == story_id)
    if status:
        query = query.filter(GapReport.status == status)
    items = query.order_by(GapReport.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "story_id": item.story_id,
                "description": item.description,
                "status": item.status,
                "votes_count": item.votes_count,
            }
            for item in items
        ]
    }

@router.post("/gap_reports")
def create_report(request: Request, payload: GapReportCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    user_id = resolve_user_id(db, request.state.user)
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user id")
    item = GapReport(
        id=uuid4(),
        user_id=user_id,
        story_id=payload.story_id,
        description=payload.description,
        status="open",
    )
    db.add(item)
    db.commit()
    safe_record_audit(
        db,
        action="collaboration.gap_report_created",
        object_type="gap_report",
        object_id=str(item.id),
        actor_user_id=user_id,
        actor_subject_value=actor_subject(getattr(request.state, "user", None)),
        request_id=str(getattr(request.state, "request_id", "")) or None,
        details={"story_id": payload.story_id, "status": item.status},
    )
    try:
        ok, _ = publish_event(
            get_redis(REDIS_URL),
            "simulation.events",
            events.build_event(
                events.GAP_REPORTED,
                user_id=user_id,
                source_service="collaboration-service",
                request_id=getattr(request.state, "request_id", None),
                story_id=payload.story_id or "",
            ),
            maxlen=EVENT_STREAM_MAXLEN,
        )
        if not ok:
            logger.warning("Failed to publish gap_reported event", extra={"gap_report_id": str(item.id)})
    except Exception as exc:
        logger.warning(
            "Error while publishing gap_reported event",
            extra={"gap_report_id": str(item.id), "error": str(exc)},
        )
    return {"id": str(item.id), "story_id": item.story_id, "description": item.description, "status": item.status}


@router.patch("/gap_reports/{report_id}")
def update_report(
    request: Request,
    report_id: str,
    payload: GapReportUpdate,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator"])
    item = db.query(GapReport).filter(GapReport.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if payload.status:
        item.status = payload.status
    if payload.description:
        item.description = payload.description
    db.commit()
    return {
        "id": str(item.id),
        "story_id": item.story_id,
        "description": item.description,
        "status": item.status,
        "votes_count": item.votes_count,
    }
