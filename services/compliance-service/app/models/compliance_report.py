from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class ComplianceReport(Base):
    __tablename__ = "compliance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id"))
    story_code = Column(String(30))
    regulations = Column(JSON)
    status = Column(String(30))
    report = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
