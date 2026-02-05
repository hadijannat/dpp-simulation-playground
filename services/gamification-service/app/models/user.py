from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    keycloak_id = Column(String(255), unique=True)
    email = Column(String(255))
    display_name = Column(String(255))
    organization = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
