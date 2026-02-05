from sqlalchemy import Column, String, JSON
from .base import Base


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True)
    result = Column(JSON, default=dict)
