from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.story_progress import StoryProgress
from ...auth import require_roles

router = APIRouter()

@router.get("/progress")
def get_progress(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    user_id = request.state.user.get("sub")
    if not user_id:
        return {"progress": []}
    items = (
        db.query(StoryProgress)
        .filter(StoryProgress.user_id == user_id)
        .order_by(StoryProgress.started_at.desc())
        .all()
    )
    return {
        "progress": [
            {
                "id": str(item.id),
                "story_id": item.story_id,
                "status": item.status,
                "completion_percentage": item.completion_percentage,
                "steps_completed": item.steps_completed,
            }
            for item in items
        ]
    }
