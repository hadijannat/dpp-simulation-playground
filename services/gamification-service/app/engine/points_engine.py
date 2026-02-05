from datetime import date, timedelta
from uuid import uuid4
from ..core.db import SessionLocal
from ..models.user_points import UserPoints


def add_points(user_id: str, points: int, event_date: date | None = None) -> UserPoints:
    db = SessionLocal()
    try:
        event_date = event_date or date.today()
        record = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        if not record:
            record = UserPoints(id=uuid4(), user_id=user_id, total_points=0, level=1)
            db.add(record)
        record.total_points = (record.total_points or 0) + points
        last_date = record.last_activity_date
        if last_date == event_date:
            pass
        elif last_date == event_date - timedelta(days=1):
            record.current_streak_days = (record.current_streak_days or 0) + 1
        else:
            record.current_streak_days = 1
        record.longest_streak_days = max(record.longest_streak_days or 0, record.current_streak_days or 0)
        record.last_activity_date = event_date
        record.level = max(1, int((record.total_points or 0) / 100) + 1)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()
