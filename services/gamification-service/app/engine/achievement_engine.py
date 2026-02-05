import yaml
import os
from typing import List, Dict
from uuid import uuid4
from sqlalchemy.orm import Session
from ..models.achievement import Achievement

DEFINITIONS = os.path.join(os.path.dirname(__file__), "..", "definitions", "achievements.yaml")


def load_achievements() -> List[Dict]:
    with open(DEFINITIONS, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def ensure_achievements(db: Session) -> None:
    definitions = load_achievements()
    for definition in definitions:
        code = definition.get("code")
        if not code:
            continue
        existing = db.query(Achievement).filter(Achievement.code == code).first()
        if existing:
            continue
        record = Achievement(
            id=uuid4(),
            code=code,
            name=definition.get("name"),
            description=definition.get("description"),
            points=definition.get("points", 0),
            criteria=definition.get("criteria", {}),
            category=definition.get("category"),
        )
        db.add(record)
    db.commit()
