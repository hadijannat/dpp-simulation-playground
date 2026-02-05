from fastapi import APIRouter, Request
from ...core.story_loader import load_story
from ...auth import require_roles

router = APIRouter()

@router.get("/stories/{code}")
def get_story(request: Request, code: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return load_story(code)

@router.post("/sessions/{session_id}/stories/{code}/start")
def start_story(request: Request, session_id: str, code: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    story = load_story(code)
    return {"session_id": session_id, "story": story, "status": "started"}
