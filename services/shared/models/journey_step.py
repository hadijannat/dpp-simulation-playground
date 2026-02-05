from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import text
from .base import Base


class JourneyStep(Base):
    __tablename__ = "journey_steps"
    __table_args__ = (
        UniqueConstraint("template_id", "step_key"),
        UniqueConstraint("template_id", "order_index"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("journey_templates.id", ondelete="CASCADE"))
    step_key = Column(String(120), nullable=False)
    title = Column(String(255), nullable=False)
    action = Column(String(120), nullable=False)
    order_index = Column(Integer, nullable=False)
    help_text = Column(Text)
    default_payload = Column(JSONB, server_default=text("'{}'::jsonb"))
