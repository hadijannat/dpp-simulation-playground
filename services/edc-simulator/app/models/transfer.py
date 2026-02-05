from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class EdcTransfer(Base):
    __tablename__ = "edc_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True)
    transfer_id = Column(String(255), unique=True, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id"))
    asset_id = Column(String(255))
    consumer_participant_id = Column(String(255))
    provider_participant_id = Column(String(255))
    current_state = Column(String(30))
    state_history = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
