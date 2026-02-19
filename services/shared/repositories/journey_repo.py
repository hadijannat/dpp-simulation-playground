from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.journey_template import JourneyTemplate
from ..models.journey_step import JourneyStep
from ..models.journey_run import JourneyRun
from ..models.journey_step_run import JourneyStepRun


def get_template_by_code(db: Session, code: str) -> JourneyTemplate | None:
    return db.query(JourneyTemplate).filter(JourneyTemplate.code == code).first()


def list_active_templates(db: Session) -> list[JourneyTemplate]:
    return db.query(JourneyTemplate).filter(JourneyTemplate.is_active.is_(True)).all()


def list_steps_for_template(db: Session, template_id) -> list[JourneyStep]:
    return (
        db.query(JourneyStep)
        .filter(JourneyStep.template_id == template_id)
        .order_by(JourneyStep.order_index)
        .all()
    )


def create_run(
    db: Session,
    template_id,
    user_id,
    role: str,
    locale: str,
    metadata: dict | None = None,
    session_id=None,
) -> JourneyRun:
    first_step = (
        db.query(JourneyStep)
        .filter(JourneyStep.template_id == template_id)
        .order_by(JourneyStep.order_index)
        .first()
    )
    run = JourneyRun(
        id=uuid4(),
        template_id=template_id,
        user_id=user_id,
        active_role=role,
        locale=locale,
        status="active",
        current_step_key=first_step.step_key if first_step else None,
        session_id=session_id,
        metadata_=metadata or {},
    )
    db.add(run)
    db.flush()
    db.refresh(run)
    return run


def get_run(db: Session, run_id) -> JourneyRun | None:
    return db.query(JourneyRun).filter(JourneyRun.id == run_id).first()


def get_run_with_steps(db: Session, run_id) -> dict | None:
    run = db.query(JourneyRun).filter(JourneyRun.id == run_id).first()
    if not run:
        return None
    step_runs = (
        db.query(JourneyStepRun)
        .filter(JourneyStepRun.journey_run_id == run_id)
        .order_by(JourneyStepRun.executed_at)
        .all()
    )
    return {"run": run, "step_runs": step_runs}


def create_step_run(
    db: Session,
    run_id,
    step_key: str,
    payload: dict | None = None,
    result: dict | None = None,
    metadata: dict | None = None,
) -> JourneyStepRun:
    step_run = JourneyStepRun(
        id=uuid4(),
        journey_run_id=run_id,
        step_key=step_key,
        status="completed",
        payload=payload or {},
        result=result or {},
        metadata_=metadata or {},
    )
    db.add(step_run)
    db.flush()
    db.refresh(step_run)
    return step_run


def update_run_step(db: Session, run: JourneyRun, step_key: str) -> None:
    run.current_step_key = step_key
    run.updated_at = datetime.now(timezone.utc)
    db.flush()
