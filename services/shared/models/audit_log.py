from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    action = Column(String(120), nullable=False, index=True)

    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    actor_subject = Column(String(255), nullable=True)

    object_type = Column(String(80), nullable=False, index=True)
    object_id = Column(String(128), nullable=False, index=True)

    session_id = Column(String(64), nullable=True, index=True)
    run_id = Column(String(64), nullable=True, index=True)
    request_id = Column(String(128), nullable=True, index=True)

    payload_hash = Column(String(64), nullable=False)
    details = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
