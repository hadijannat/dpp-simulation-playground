from fastapi import APIRouter, Request, Depends, HTTPException
from ...schemas.annotation_schema import AnnotationCreate
from uuid import UUID, uuid4
import logging
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.annotation import Annotation
from ...config import REDIS_URL, EVENT_STREAM_MAXLEN
from ...auth import require_roles
from services.shared import events
from services.shared.outbox import emit_event
from services.shared.user_registry import resolve_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/annotations")
def list_annotations(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    target_element: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(
        request.state.user, ["developer", "admin", "regulator", "manufacturer"]
    )
    query = db.query(Annotation)
    if story_id is not None:
        query = query.filter(Annotation.story_id == story_id)
    if status:
        query = query.filter(Annotation.status == status)
    if target_element:
        query = query.filter(Annotation.target_element == target_element)
    items = (
        query.order_by(Annotation.created_at.desc()).offset(offset).limit(limit).all()
    )
    return {
        "items": [
            {
                "id": str(item.id),
                "story_id": item.story_id,
                "target_element": item.target_element,
                "annotation_type": item.annotation_type,
                "content": item.content,
                "status": item.status,
                "votes_count": item.votes_count,
            }
            for item in items
        ]
    }


@router.post("/annotations")
def create_annotation(
    request: Request, payload: AnnotationCreate, db: Session = Depends(get_db)
):
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
    item = Annotation(
        id=uuid4(),
        user_id=user_id,
        story_id=payload.story_id,
        target_element=payload.target_element,
        annotation_type=payload.annotation_type,
        content=payload.content,
        status="open",
    )
    db.add(item)
    db.commit()
    try:
        ok, _ = emit_event(
            db,
            stream="simulation.events",
            payload=events.build_event(
                events.ANNOTATION_CREATED,
                user_id=str(user_id),
                source_service="collaboration-service",
                request_id=getattr(request.state, "request_id", None),
                story_id=str(payload.story_id) if payload.story_id is not None else "",
                metadata={
                    "annotation_id": str(item.id),
                    "annotation_type": payload.annotation_type,
                    "target_element": payload.target_element,
                },
            ),
            redis_url=REDIS_URL,
            maxlen=EVENT_STREAM_MAXLEN,
            commit=True,
            log=logger,
        )
        if not ok:
            logger.warning(
                "Failed to publish annotation_created event",
                extra={"annotation_id": str(item.id)},
            )
    except Exception as exc:
        logger.warning(
            "Error while publishing annotation_created event",
            extra={"annotation_id": str(item.id), "error": str(exc)},
        )
    return {
        "id": str(item.id),
        "story_id": item.story_id,
        "target_element": item.target_element,
        "annotation_type": item.annotation_type,
        "content": item.content,
        "status": item.status,
    }
