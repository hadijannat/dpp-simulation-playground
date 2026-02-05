from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.gap_report import GapReport
from ...config import REDIS_URL
from redis import Redis
from ...auth import require_roles

router = APIRouter()

class GapReportCreate(BaseModel):
    story_id: int | None = None
    description: str

@router.get("/gap_reports")
def list_reports(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(GapReport)
    if story_id is not None:
        query = query.filter(GapReport.story_id == story_id)
    if status:
        query = query.filter(GapReport.status == status)
    items = query.order_by(GapReport.created_at.desc()).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "story_id": item.story_id,
                "description": item.description,
                "status": item.status,
            }
            for item in items
        ]
    }

@router.post("/gap_reports")
def create_report(request: Request, payload: GapReportCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = GapReport(
        id=uuid4(),
        user_id=request.state.user.get("sub"),
        story_id=payload.story_id,
        description=payload.description,
        status="open",
    )
    db.add(item)
    db.commit()
    try:
        Redis.from_url(REDIS_URL).xadd(
            "simulation.events",
            {
                "event_type": "gap_reported",
                "user_id": request.state.user.get("sub"),
                "story_id": payload.story_id or "",
            },
        )
    except Exception:
        pass
    return {"id": str(item.id), "story_id": item.story_id, "description": item.description, "status": item.status}
