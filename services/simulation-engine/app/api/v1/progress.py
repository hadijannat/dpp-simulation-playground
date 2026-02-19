from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from ...models.session import SimulationSession
from ...models.story import UserStory
from ...models.story_progress import StoryProgress
from services.shared.user_registry import resolve_user_id

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]
PRIVILEGED_PROGRESS_ROLES = {"admin", "developer", "regulator"}


def _resolve_target_user_id(
    request: Request,
    db: Session,
    user_id_param: str | None,
) -> str | None:
    if user_id_param:
        user_roles = set((request.state.user or {}).get("realm_access", {}).get("roles", []))
        if not user_roles.intersection(PRIVILEGED_PROGRESS_ROLES):
            raise HTTPException(status_code=403, detail="Insufficient role to query other users")
        return user_id_param
    return resolve_user_id(db, request.state.user)


def _error_count(validation_results: Any) -> int:
    if not isinstance(validation_results, dict):
        return 0
    count = 0
    if validation_results.get("status") == "error":
        count += 1
    summary = validation_results.get("summary")
    if isinstance(summary, dict):
        violations = summary.get("violations", 0)
        if isinstance(violations, int) and violations > 0:
            count += violations
    nested_result = validation_results.get("result")
    if isinstance(nested_result, dict) and nested_result.get("status") == "error":
        count += 1
    return count


@router.get("/progress")
def get_progress(
    request: Request,
    session_id: str | None = None,
    role: str | None = None,
    status: str | None = None,
    story_code: str | None = None,
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)
    target_user_id = _resolve_target_user_id(request, db, user_id)
    if not target_user_id:
        return {"items": [], "total": 0, "limit": limit, "offset": offset, "progress": []}

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    query = (
        db.query(StoryProgress, UserStory.code.label("story_code"))
        .outerjoin(UserStory, StoryProgress.story_id == UserStory.id)
        .filter(StoryProgress.user_id == target_user_id)
    )
    if role:
        query = query.filter(StoryProgress.role_type == role)
    if status:
        query = query.filter(StoryProgress.status == status)
    if story_code:
        query = query.filter(UserStory.code == story_code)
    if session_id:
        session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not session:
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "progress": []}
        if str(session.user_id) != str(target_user_id):
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "progress": []}
        if session.current_story_id:
            query = query.filter(StoryProgress.story_id == session.current_story_id)

    total = query.count()
    rows = (
        query.order_by(StoryProgress.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = []
    for progress, progress_story_code in rows:
        time_spent = progress.time_spent_seconds or 0
        if not time_spent and progress.started_at and progress.completed_at:
            time_spent = int((progress.completed_at - progress.started_at).total_seconds())
        items.append(
            {
                "id": str(progress.id),
                "story_id": progress.story_id,
                "story_code": progress_story_code,
                "role_type": progress.role_type,
                "status": progress.status,
                "completion_percentage": progress.completion_percentage,
                "steps_completed": progress.steps_completed,
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "time_spent_seconds": time_spent,
                "error_count": _error_count(progress.validation_results),
            }
        )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        # Backward-compatible alias.
        "progress": items,
    }


@router.get("/progress/epics")
def get_epic_progress(
    request: Request,
    role: str | None = None,
    status: str | None = None,
    user_id: str | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)
    target_user_id = _resolve_target_user_id(request, db, user_id)
    if not target_user_id:
        return {"epics": []}

    join_condition = (
        (StoryProgress.story_id == UserStory.id)
        & (StoryProgress.user_id == target_user_id)
    )
    if role:
        join_condition = join_condition & (StoryProgress.role_type == role)
    if status:
        join_condition = join_condition & (StoryProgress.status == status)

    rows = (
        db.query(UserStory.epic_id, UserStory.id, StoryProgress.status)
        .outerjoin(StoryProgress, join_condition)
        .all()
    )
    totals: dict[int | None, dict[str, int]] = {}
    for epic_id, _story_id, item_status in rows:
        entry = totals.setdefault(epic_id, {"total": 0, "completed": 0})
        entry["total"] += 1
        if item_status == "completed":
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
