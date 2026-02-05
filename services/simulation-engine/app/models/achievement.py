from sqlalchemy import Column, Integer, String, Text, JSON
from .base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    points = Column(Integer, default=0)
    rarity = Column(String(20), default="common")
    criteria = Column(JSON, nullable=False)
    category = Column(String(50))
