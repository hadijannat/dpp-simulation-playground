from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class GapReport(Base):
    __tablename__ = "gap_reports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    story_id = Column(Integer, ForeignKey("user_stories.id"))
    description = Column(Text, nullable=False)
    status = Column(String(30), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
