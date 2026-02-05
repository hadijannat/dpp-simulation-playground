from sqlalchemy import Column, DateTime, ForeignKey, JSON, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())
    context = Column(JSON)
