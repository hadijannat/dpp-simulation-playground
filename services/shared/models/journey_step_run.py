from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class JourneyStepRun(Base):
    __tablename__ = "journey_step_runs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    journey_run_id = Column(UUID(as_uuid=True), ForeignKey("journey_runs.id", ondelete="CASCADE"), nullable=False)
    step_key = Column(String(120), nullable=False)
    status = Column(String(30), server_default="completed")
    payload = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    metadata_ = Column("metadata", JSON, default=dict)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
