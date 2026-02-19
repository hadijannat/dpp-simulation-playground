from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from .base import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)
    user_id = Column(String(120), nullable=False, default="")
    source_service = Column(String(80), nullable=False, index=True)
    version = Column(String(16), nullable=False, default="1")

    session_id = Column(String(64), index=True)
    run_id = Column(String(64), index=True)
    request_id = Column(String(128), index=True)

    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    stream = Column(String(120), nullable=False, default="simulation.events")
    stream_message_id = Column(String(64))

    published = Column(Boolean, nullable=False, default=True)
    publish_error = Column(Text)

    metadata_ = Column("metadata", JSON, default=dict)
    payload = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
