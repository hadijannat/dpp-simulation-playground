from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from .base import Base


class PointRule(Base):
    __tablename__ = "point_rules"

    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), unique=True, nullable=False, index=True)
    points = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    rule_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
