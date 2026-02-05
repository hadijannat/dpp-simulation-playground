from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class DigitalTwinEdge(Base):
    __tablename__ = "digital_twin_edges"
    __table_args__ = (UniqueConstraint("snapshot_id", "edge_key"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("digital_twin_snapshots.id", ondelete="CASCADE"), nullable=False)
    edge_key = Column(String(120), nullable=False)
    source_node_key = Column(String(120), nullable=False)
    target_node_key = Column(String(120), nullable=False)
    label = Column(String(255))
    payload = Column(JSON, default=dict)
