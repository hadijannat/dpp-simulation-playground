from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.comment import Comment
from ...auth import require_roles

router = APIRouter()

class CommentCreate(BaseModel):
    target_id: str
    content: str

@router.get("/comments")
def list_comments(request: Request, target_id: str | None = None, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(Comment)
    if target_id:
        query = query.filter(Comment.target_id == target_id)
    items = query.order_by(Comment.created_at.desc()).all()
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
    item = Comment(
        id=uuid4(),
        user_id=request.state.user.get("sub"),
        target_id=payload.target_id,
        content=payload.content,
    )
    db.add(item)
    db.commit()
    return {"id": str(item.id), "target_id": item.target_id, "content": item.content}
