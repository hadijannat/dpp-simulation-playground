from sqlalchemy import Column, String, DateTime, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class ComplianceRuleVersion(Base):
    __tablename__ = "compliance_rule_versions"
    __table_args__ = (UniqueConstraint("regulation", "version"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    regulation = Column(String(120), nullable=False)
    version = Column(String(40), nullable=False)
    rules = Column(JSON, default=dict)
    effective_from = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
