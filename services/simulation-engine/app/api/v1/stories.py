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
    return {"items": list_stories()}

@router.get("/stories/{code}")
def get_story(request: Request, code: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return load_story(code)

@router.post("/sessions/{session_id}/stories/{code}/start")
def start_story(request: Request, session_id: str, code: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    story = load_story(code)
    story_record = db.query(UserStory).filter(UserStory.code == code).first()
    progress = StoryProgress(
        id=uuid4(),
        user_id=session.user_id,
        story_id=story_record.id if story_record else None,
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
    return {"session_id": session_id, "story": story, "status": "started", "progress_id": str(progress.id)}


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
