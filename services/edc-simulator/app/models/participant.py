from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class EdcParticipant(Base):
    __tablename__ = "edc_participants"

    id = Column(UUID(as_uuid=True), primary_key=True)
    participant_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    metadata = Column(JSON, default=dict)
