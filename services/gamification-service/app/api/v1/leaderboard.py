from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_points import UserPoints
from ...auth import require_roles

router = APIRouter()

@router.get("/leaderboard")
def leaderboard(request: Request, limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    items = (
        db.query(UserPoints)
        .order_by(UserPoints.total_points.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {"user_id": str(item.user_id), "total_points": item.total_points, "level": item.level}
            for item in items
        ]
    }
