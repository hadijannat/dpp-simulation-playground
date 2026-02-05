from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class StoryProgress(Base):
    __tablename__ = "story_progress"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    story_id = Column(Integer, ForeignKey("user_stories.id"))
    role_type = Column(String(50), nullable=False)
    status = Column(String(30), default="not_started")
    completion_percentage = Column(Integer, default=0)
    steps_completed = Column(JSON, default=list)
    validation_results = Column(JSON)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    time_spent_seconds = Column(Integer, default=0)
