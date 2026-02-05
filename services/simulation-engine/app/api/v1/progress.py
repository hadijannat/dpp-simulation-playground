from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.story_progress import StoryProgress
from ...models.story import UserStory
from ...auth import require_roles
from services.shared.user_registry import resolve_user_id

router = APIRouter()

@router.get("/progress")
def get_progress(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    user_id = resolve_user_id(db, request.state.user)
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


@router.get("/progress/epics")
def get_epic_progress(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    user_id = resolve_user_id(db, request.state.user)
    if not user_id:
        return {"epics": []}
    rows = (
        db.query(UserStory.epic_id, UserStory.id, StoryProgress.status)
        .outerjoin(
            StoryProgress,
            (StoryProgress.story_id == UserStory.id)
            & (StoryProgress.user_id == user_id),
        )
        .all()
    )
    totals = {}
    for epic_id, story_id, status in rows:
        entry = totals.setdefault(epic_id, {"total": 0, "completed": 0})
        entry["total"] += 1
        if status == "completed":
            entry["completed"] += 1
    items = []
    for epic_id, counts in totals.items():
        total = counts["total"]
        completed = counts["completed"]
        percent = int((completed / total) * 100) if total else 0
        items.append(
            {
                "epic_id": epic_id,
                "total_stories": total,
                "completed_stories": completed,
                "completion_percentage": percent,
            }
        )
    return {"epics": items}
