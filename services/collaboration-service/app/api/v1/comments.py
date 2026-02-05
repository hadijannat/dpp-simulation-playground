from fastapi import APIRouter, Request
from pydantic import BaseModel
from uuid import uuid4
from ...auth import require_roles

router = APIRouter()
_store = []

class CommentCreate(BaseModel):
    target_id: str
    content: str

@router.get("/comments")
def list_comments(request: Request):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    return {"items": _store}

@router.post("/comments")
def create_comment(request: Request, payload: CommentCreate):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
