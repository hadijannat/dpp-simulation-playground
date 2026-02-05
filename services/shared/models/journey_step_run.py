from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
from .base import Base


class JourneyStepRun(Base):
    __tablename__ = "journey_step_runs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    journey_run_id = Column(UUID(as_uuid=True), ForeignKey("journey_runs.id", ondelete="CASCADE"), nullable=False)
    step_key = Column(String(120), nullable=False)
    status = Column(String(30), server_default="completed")
    payload = Column(JSONB, server_default=text("'{}'::jsonb"))
    result = Column(JSONB, server_default=text("'{}'::jsonb"))
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
