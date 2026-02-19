from __future__ import annotations

import os
from typing import Dict

import yaml
from sqlalchemy.orm import Session

from ..models.point_rule import PointRule

POINT_RULE_DEFINITIONS = os.path.join(os.path.dirname(__file__), "..", "definitions", "point_rules.yaml")


def load_point_rules_from_yaml() -> Dict[str, int]:
    if not os.path.exists(POINT_RULE_DEFINITIONS):
        return {}
    with open(POINT_RULE_DEFINITIONS, "r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    rules: Dict[str, int] = {}
    for event_type, points in loaded.items():
        try:
            rules[str(event_type)] = int(points)
        except Exception:
            continue
    return rules


def ensure_point_rules(db: Session) -> None:
    seeded = load_point_rules_from_yaml()
    for event_type, points in seeded.items():
        existing = db.query(PointRule).filter(PointRule.event_type == event_type).first()
        if existing:
            continue
        db.add(PointRule(event_type=event_type, points=points, is_active=True, rule_metadata={"seed": "yaml"}))
    db.commit()


def load_active_point_rules(db: Session) -> Dict[str, int]:
    rows = (
        db.query(PointRule)
        .filter(PointRule.is_active.is_(True))
        .order_by(PointRule.event_type.asc())
        .all()
    )
    return {row.event_type: int(row.points or 0) for row in rows}
