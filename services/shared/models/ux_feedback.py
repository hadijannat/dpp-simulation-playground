from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class UxFeedback(Base):
    __tablename__ = "ux_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    journey_run_id = Column(UUID(as_uuid=True), ForeignKey("journey_runs.id", ondelete="SET NULL"))
    locale = Column(String(10), server_default="en")
    role = Column(String(50), nullable=False)
    flow = Column(String(120), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
