from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class DigitalTwinSnapshot(Base):
    __tablename__ = "digital_twin_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True)
    dpp_instance_id = Column(UUID(as_uuid=True), ForeignKey("dpp_instances.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(255))
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
