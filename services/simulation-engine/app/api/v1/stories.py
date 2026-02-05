from fastapi import APIRouter
from ...core.story_loader import load_story

router = APIRouter()

@router.get("/stories/{code}")
def get_story(code: str):
    return load_story(code)

@router.post("/sessions/{session_id}/stories/{code}/start")
def start_story(session_id: str, code: str):
    story = load_story(code)
    return {"session_id": session_id, "story": story, "status": "started"}
