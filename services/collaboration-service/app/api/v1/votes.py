from fastapi import APIRouter, Request
from pydantic import BaseModel
from uuid import uuid4
from ...auth import require_roles

router = APIRouter()
_store = []

class VoteCreate(BaseModel):
    target_id: str
    value: int

@router.get("/votes")
def list_votes(request: Request):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    return {"items": _store}

@router.post("/votes")
def create_vote(request: Request, payload: VoteCreate):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
