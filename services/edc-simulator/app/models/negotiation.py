from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class EdcNegotiation(Base):
    __tablename__ = "edc_negotiations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id"))
    negotiation_id = Column(String(255), unique=True, nullable=False)
    provider_participant_id = Column(String(255))
    consumer_participant_id = Column(String(255))
    asset_id = Column(String(255))
    current_state = Column(String(30))
    policy_odrl = Column(JSON, default=dict)
    state_history = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
