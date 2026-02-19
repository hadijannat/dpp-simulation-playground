from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_achievement import UserAchievement
from ...models.achievement import Achievement
from ...auth import require_roles

router = APIRouter()

@router.get("/achievements")
def list_achievements(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    items = db.query(Achievement).order_by(Achievement.code.asc()).all()
    return {
        "items": [
            {
                "code": item.code,
                "name": item.name,
                "description": item.description,
                "points": int(item.points or 0),
                "criteria": item.criteria or {},
                "category": item.category,
            }
            for item in items
        ]
    }


@router.get("/achievements/{user_id}")
def list_user_achievements(request: Request, user_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    rows = (
        db.query(UserAchievement, Achievement)
        .join(Achievement, UserAchievement.achievement_id == Achievement.id)
        .filter(UserAchievement.user_id == user_id)
        .all()
    )
    return {
        "items": [
            {
                "code": achievement.code,
                "name": achievement.name,
                "points": achievement.points,
                "awarded_at": record.awarded_at.isoformat() if record.awarded_at else None,
            }
            for record, achievement in rows
        ]
    }
