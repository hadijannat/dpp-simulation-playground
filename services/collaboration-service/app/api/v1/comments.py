from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.comment import Comment
from ...auth import require_roles
from services.shared.user_registry import resolve_user_id

router = APIRouter()

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
    user_id = resolve_user_id(db, request.state.user)
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user id")
    item = Comment(
        id=uuid4(),
        user_id=user_id,
        target_id=payload.target_id,
        content=payload.content,
    )
    db.add(item)
    db.commit()
    return {"id": str(item.id), "target_id": item.target_id, "content": item.content}
