from fastapi import APIRouter, Request
from pydantic import BaseModel
from uuid import uuid4
from ...auth import require_roles

router = APIRouter()
_store = []

class GapReportCreate(BaseModel):
    story_id: int | None = None
    description: str

@router.get("/gap_reports")
def list_reports(request: Request):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    return {"items": _store}

@router.post("/gap_reports")
def create_report(request: Request, payload: GapReportCreate):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
