from fastapi import APIRouter
from pydantic import BaseModel
from ...engine.points_engine import add_points

router = APIRouter()

class PointsRequest(BaseModel):
    user_id: str
    points: int

@router.post("/points")
def add(payload: PointsRequest):
    record = add_points(payload.user_id, payload.points)
    return {"user_id": str(record.user_id), "total_points": record.total_points}
