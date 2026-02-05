from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    story_id = Column(Integer, ForeignKey("user_stories.id"))
    target_element = Column(String(255))
    annotation_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    screenshot_url = Column(String(500))
    status = Column(String(30), default="open")
    votes_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
