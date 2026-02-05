from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    active_role = Column(String(50), nullable=False)
    current_story_id = Column(Integer, ForeignKey("user_stories.id"), nullable=True)
    session_state = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    journey_run_id = Column(UUID(as_uuid=True), ForeignKey("journey_runs.id", ondelete="SET NULL"), nullable=True)
