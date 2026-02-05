from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()
_store = []

class VoteCreate(BaseModel):
    target_id: str
    value: int

@router.get("/votes")
def list_votes():
    return {"items": _store}

@router.post("/votes")
def create_vote(payload: VoteCreate):
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
