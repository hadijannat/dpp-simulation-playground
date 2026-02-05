from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.vote import Vote
from ...models.annotation import Annotation
from ...auth import require_roles

router = APIRouter()

class VoteCreate(BaseModel):
    target_id: str
    value: int

@router.get("/votes")
def list_votes(request: Request, target_id: str | None = None, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(Vote)
    if target_id:
        query = query.filter(Vote.target_id == target_id)
    items = query.order_by(Vote.created_at.desc()).all()
    return {
        "items": [
            {"id": str(item.id), "target_id": item.target_id, "value": item.value}
            for item in items
        ]
    }

@router.post("/votes")
def create_vote(request: Request, payload: VoteCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    user_id = request.state.user.get("sub")
    existing = db.query(Vote).filter(Vote.user_id == user_id, Vote.target_id == payload.target_id).first()
    if existing:
        return {"id": str(existing.id), "target_id": existing.target_id, "value": existing.value}
    item = Vote(id=uuid4(), user_id=user_id, target_id=payload.target_id, value=payload.value)
    db.add(item)
    annotation = db.query(Annotation).filter(Annotation.id == payload.target_id).first()
    if annotation:
        annotation.votes_count = (annotation.votes_count or 0) + payload.value
    db.commit()
    return {"id": str(item.id), "target_id": item.target_id, "value": item.value}
