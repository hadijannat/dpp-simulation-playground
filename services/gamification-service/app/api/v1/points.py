from fastapi import APIRouter, Request
from pydantic import BaseModel
from ...engine.points_engine import add_points
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
