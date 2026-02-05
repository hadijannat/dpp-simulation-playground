from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
from .base import Base


class ComplianceRunFix(Base):
    __tablename__ = "compliance_run_fixes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("compliance_reports.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)
    value = Column(JSONB, server_default=text("'null'::jsonb"))
    applied_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
