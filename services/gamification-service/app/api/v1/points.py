from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from ...engine.points_engine import add_points
from ...core.db import get_db
from sqlalchemy.orm import Session
from ...models.user_points import UserPoints
from ...auth import require_roles

router = APIRouter()

class PointsRequest(BaseModel):
    user_id: str
    points: int

@router.post("/points")
def add(request: Request, payload: PointsRequest):
    require_roles(request.state.user, ["developer", "admin"])
    record = add_points(payload.user_id, payload.points)
    return {"user_id": str(record.user_id), "total_points": record.total_points}


@router.get("/points/{user_id}")
def get_points(request: Request, user_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    record = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "user_id": str(record.user_id),
        "total_points": record.total_points,
        "level": record.level,
        "current_streak_days": record.current_streak_days,
        "longest_streak_days": record.longest_streak_days,
    }
