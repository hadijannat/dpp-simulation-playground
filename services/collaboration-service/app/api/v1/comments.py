from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
import logging
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.comment import Comment
from ...config import REDIS_URL, EVENT_STREAM_MAXLEN
from ...auth import require_roles
from services.shared import events
from services.shared.redis_client import get_redis, publish_event
from services.shared.user_registry import resolve_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

class CommentCreate(BaseModel):
    target_id: str
    content: str

@router.get("/comments")
def list_comments(
    request: Request,
    target_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(Comment)
    if target_id:
        query = query.filter(Comment.target_id == target_id)
    items = query.order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "target_id": item.target_id,
                "content": item.content,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ]
    }

@router.post("/comments")
def create_comment(request: Request, payload: CommentCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    raw_user_id = resolve_user_id(db, request.state.user)
    if not raw_user_id:
        raise HTTPException(status_code=400, detail="Missing user id")
    try:
        user_id = UUID(str(raw_user_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc
    item = Comment(
        id=uuid4(),
        user_id=user_id,
        target_id=payload.target_id,
        content=payload.content,
    )
    db.add(item)
    db.commit()
    try:
        ok, _ = publish_event(
            get_redis(REDIS_URL),
            "simulation.events",
            events.build_event(
                events.COMMENT_ADDED,
                user_id=str(user_id),
                source_service="collaboration-service",
                request_id=getattr(request.state, "request_id", None),
                metadata={
                    "comment_id": str(item.id),
                    "target_id": payload.target_id,
                },
            ),
            maxlen=EVENT_STREAM_MAXLEN,
        )
        if not ok:
            logger.warning("Failed to publish comment_added event", extra={"comment_id": str(item.id)})
    except Exception as exc:
        logger.warning(
            "Error while publishing comment_added event",
            extra={"comment_id": str(item.id), "error": str(exc)},
        )
    return {"id": str(item.id), "target_id": item.target_id, "content": item.content}
