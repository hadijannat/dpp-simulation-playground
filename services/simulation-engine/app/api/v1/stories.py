from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.story_loader import load_story, list_stories
from ...core.db import get_db
from ...models.story import UserStory
from ...models.story_progress import StoryProgress
from ...models.session import SimulationSession
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
from ...auth import require_roles

router = APIRouter()

@router.get("/stories")
def get_stories(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    try:
        items = list_stories()
    except KeyError:
        items = []
    return {"items": items}

@router.get("/stories/{code}")
def get_story(request: Request, code: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    try:
        return load_story(code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Story not found")

@router.post("/sessions/{session_id}/stories/{code}/start")
def start_story(request: Request, session_id: str, code: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        story = load_story(code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Story not found")
    story_record = db.query(UserStory).filter(UserStory.code == code).first()
    story_id = story_record.id if story_record else None
    progress = db.query(StoryProgress).filter(
        StoryProgress.user_id == session.user_id,
        StoryProgress.story_id == story_id,
        StoryProgress.role_type == session.active_role,
    ).first()
    existing = progress is not None
    if progress:
        # Restart story progress to avoid unique constraint violations.
        progress.status = "in_progress"
        progress.completion_percentage = 0
        progress.steps_completed = []
        progress.validation_results = None
        progress.started_at = datetime.now(timezone.utc)
        progress.completed_at = None
        progress.time_spent_seconds = 0
    else:
        progress = StoryProgress(
            id=uuid4(),
            user_id=session.user_id,
            story_id=story_id,
            role_type=session.active_role,
            status="in_progress",
            completion_percentage=0,
            steps_completed=[],
            started_at=datetime.now(timezone.utc),
        )
        db.add(progress)
    session.current_story_id = story_record.id if story_record else None
    session.session_state = {**(session.session_state or {}), "story_code": code}
    session.last_activity = datetime.now(timezone.utc)
    db.commit()
    status = "restarted" if existing else "started"
    return {"session_id": session_id, "story": story, "status": status, "progress_id": str(progress.id)}


class StoryValidateRequest(BaseModel):
    data: dict
    regulations: list[str] = []


@router.post("/sessions/{session_id}/stories/{code}/validate")
def validate_story(request: Request, session_id: str, code: str, payload: StoryValidateRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return {
        "session_id": session_id,
        "story_code": code,
        "status": "received",
        "regulations": payload.regulations,
    }
