from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from ...core.step_executor import execute_step
from ...core.event_publisher import publish_event
from ...schemas.step_schema import StepExecuteRequest
from ...core.story_loader import load_story
from ...core.db import get_db
from ...models.session import SimulationSession
from ...models.story_progress import StoryProgress
from ...auth import require_roles

router = APIRouter()

def _safe_publish(payload: dict):
    try:
        publish_event("simulation.events", payload)
    except Exception:
        return

@router.post("/sessions/{session_id}/stories/{code}/steps/{idx}/execute")
def execute(
    request: Request,
    session_id: str,
    code: str,
    idx: int,
    payload: StepExecuteRequest,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    try:
        story = load_story(code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Story not found")
    if idx < 0 or idx >= len(story.get("steps", [])):
        raise HTTPException(status_code=404, detail="Step not found")
    step = story["steps"][idx]
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    context = {
        "session_id": session_id,
        "story_code": code,
        "user_id": str(session.user_id),
        "event_id": uuid4(),
    }
    result = execute_step(db, step["action"], step.get("params", {}), payload.payload, context)

    progress_query = db.query(StoryProgress).filter(StoryProgress.user_id == session.user_id)
    if session.current_story_id:
        progress_query = progress_query.filter(StoryProgress.story_id == session.current_story_id)
    progress = progress_query.order_by(StoryProgress.started_at.desc()).first()
    if not progress:
        progress = StoryProgress(
            id=uuid4(),
            user_id=session.user_id,
            story_id=session.current_story_id,
            role_type=session.active_role,
            status="in_progress",
            completion_percentage=0,
            steps_completed=[],
            started_at=datetime.now(timezone.utc),
        )
        db.add(progress)
        db.commit()
    steps_completed = progress.steps_completed if progress and progress.steps_completed is not None else []
    if idx not in steps_completed:
        steps_completed.append(idx)
        progress.steps_completed = steps_completed
        total_steps = max(1, len(story["steps"]))
        progress.completion_percentage = int(len(steps_completed) / total_steps * 100)
        progress.validation_results = {"last_step": idx, "result": result}
        if progress.completion_percentage >= 100:
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
        session.last_activity = datetime.now(timezone.utc)
        db.commit()

    _safe_publish(
        {
            "event_type": "story_step_completed",
            "user_id": str(session.user_id),
            "session_id": session_id,
            "story_code": code,
            "step_idx": idx,
            "status": result.get("status"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"action": step.get("action")},
        }
    )
    if progress and progress.status == "completed":
        _safe_publish(
            {
                "event_type": "story_completed",
                "user_id": str(session.user_id),
                "session_id": session_id,
                "story_code": code,
                "step_idx": idx,
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {},
            }
        )
    if step.get("action") == "compliance.check" and result.get("status") == "ok":
        status = result.get("data", {}).get("status")
        if status == "compliant":
            _safe_publish(
                {
                    "event_type": "compliance_check_passed",
                    "user_id": str(session.user_id),
                    "session_id": session_id,
                    "story_code": code,
                    "step_idx": idx,
                    "status": "compliant",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {},
                }
            )
    if step.get("action") == "aas.create" and result.get("status") == "created":
        _safe_publish(
            {
                "event_type": "aas_created",
                "user_id": str(session.user_id),
                "session_id": session_id,
                "story_code": code,
                "step_idx": idx,
                "status": "created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {},
            }
        )
    if step.get("action") == "api.call" and result.get("status") == "called":
        _safe_publish(
            {
                "event_type": "api_call_success",
                "user_id": str(session.user_id),
                "session_id": session_id,
                "story_code": code,
                "step_idx": idx,
                "status": "called",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {},
            }
        )
    return {"result": result}
