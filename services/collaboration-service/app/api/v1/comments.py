from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()
_store = []

class CommentCreate(BaseModel):
    target_id: str
    content: str

@router.get("/comments")
def list_comments():
    return {"items": _store}

@router.post("/comments")
def create_comment(payload: CommentCreate):
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
