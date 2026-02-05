from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from uuid import uuid4
from ..config import DATABASE_URL
from ..models.user_points import UserPoints

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def add_points(user_id: str, points: int) -> UserPoints:
    db = SessionLocal()
    record = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not record:
        record = UserPoints(id=uuid4(), user_id=user_id, total_points=0, level=1)
        db.add(record)
    record.total_points = (record.total_points or 0) + points
    db.commit()
    db.refresh(record)
    return record
