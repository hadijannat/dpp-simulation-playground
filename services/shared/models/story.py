from sqlalchemy import Column, Integer, String, Text, JSON
from .base import Base


class UserStory(Base):
    __tablename__ = "user_stories"

    id = Column(Integer, primary_key=True)
    epic_id = Column(Integer)
    code = Column(String(30), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    acceptance_criteria = Column(JSON, nullable=False)
