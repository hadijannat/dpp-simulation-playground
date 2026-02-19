from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from .base import Base


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    stream = Column(String(120), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)

    status = Column(String(24), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_error = Column(Text, nullable=True)
    stream_message_id = Column(String(64), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
