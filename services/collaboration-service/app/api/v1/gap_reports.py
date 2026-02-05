from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()
_store = []

class GapReportCreate(BaseModel):
    story_id: int | None = None
    description: str

@router.get("/gap_reports")
def list_reports():
    return {"items": _store}

@router.post("/gap_reports")
def create_report(payload: GapReportCreate):
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
