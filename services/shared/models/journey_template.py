from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class JourneyTemplate(Base):
    __tablename__ = "journey_templates"

    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(String(80), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_role = Column(String(50), nullable=False)
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
