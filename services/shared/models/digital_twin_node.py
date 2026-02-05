from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class DigitalTwinNode(Base):
    __tablename__ = "digital_twin_nodes"
    __table_args__ = (UniqueConstraint("snapshot_id", "node_key"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("digital_twin_snapshots.id", ondelete="CASCADE"), nullable=False)
    node_key = Column(String(120), nullable=False)
    node_type = Column(String(60), nullable=False)
    label = Column(String(255), nullable=False)
    payload = Column(JSON, default=dict)
