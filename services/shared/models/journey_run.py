from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
from .base import Base


class JourneyRun(Base):
    __tablename__ = "journey_runs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("journey_templates.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    active_role = Column(String(50), nullable=False)
    locale = Column(String(10), server_default="en")
    status = Column(String(30), server_default="active")
    current_step_key = Column(String(120))
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id", ondelete="SET NULL"))
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
