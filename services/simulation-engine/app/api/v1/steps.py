from fastapi import APIRouter, Request
from ...core.step_executor import execute_step
from ...core.event_publisher import publish_event
from ...schemas.step_schema import StepExecuteRequest
from ...core.story_loader import load_story
from ...auth import require_roles

router = APIRouter()

@router.post("/sessions/{session_id}/stories/{code}/steps/{idx}/execute")
def execute(request: Request, session_id: str, code: str, idx: int, payload: StepExecuteRequest):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    story = load_story(code)
    step = story["steps"][idx]
    result = execute_step(step["action"], step.get("params", {}), payload.payload)
    publish_event("simulation.events", {"session_id": session_id, "story": code, "step": idx})
    return {"result": result}
