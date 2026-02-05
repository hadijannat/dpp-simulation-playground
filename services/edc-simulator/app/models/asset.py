from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class EdcAsset(Base):
    __tablename__ = "edc_assets"

    id = Column(UUID(as_uuid=True), primary_key=True)
    asset_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    policy_odrl = Column(JSON, default=dict)
    data_address = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
