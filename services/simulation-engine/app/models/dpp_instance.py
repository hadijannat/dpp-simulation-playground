from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class DppInstance(Base):
    __tablename__ = "dpp_instances"

    id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True))
    aas_identifier = Column(String(500), nullable=False)
    product_identifier = Column(String(255))
    product_name = Column(String(255))
    product_category = Column(String(100))
    compliance_status = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
