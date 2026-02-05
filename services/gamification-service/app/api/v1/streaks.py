from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_points import UserPoints
from ...auth import require_roles

router = APIRouter()

@router.get("/streaks")
def streaks(request: Request):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    return {"items": []}


@router.get("/streaks/{user_id}")
def streak_detail(request: Request, user_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    record = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "user_id": str(record.user_id),
        "current_streak_days": record.current_streak_days,
        "longest_streak_days": record.longest_streak_days,
        "last_activity_date": record.last_activity_date.isoformat() if record.last_activity_date else None,
    }
