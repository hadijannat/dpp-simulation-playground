from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.digital_twin_snapshot import DigitalTwinSnapshot
from ..models.digital_twin_node import DigitalTwinNode
from ..models.digital_twin_edge import DigitalTwinEdge


def get_snapshot_by_dpp(db: Session, dpp_instance_id) -> DigitalTwinSnapshot | None:
    return (
        db.query(DigitalTwinSnapshot)
        .filter(DigitalTwinSnapshot.dpp_instance_id == dpp_instance_id)
        .order_by(DigitalTwinSnapshot.created_at.desc())
        .first()
    )


def create_snapshot(
    db: Session, dpp_instance_id, label: str | None = None, metadata: dict | None = None
) -> DigitalTwinSnapshot:
    snapshot = DigitalTwinSnapshot(
        id=uuid4(),
        dpp_instance_id=dpp_instance_id,
        label=label,
        metadata_=metadata or {},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def add_node(
    db: Session,
    snapshot_id,
    node_key: str,
    node_type: str,
    label: str,
    payload: dict | None = None,
) -> DigitalTwinNode:
    node = DigitalTwinNode(
        id=uuid4(),
        snapshot_id=snapshot_id,
        node_key=node_key,
        node_type=node_type,
        label=label,
        payload=payload or {},
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def add_edge(
    db: Session,
    snapshot_id,
    edge_key: str,
    source: str,
    target: str,
    label: str | None = None,
    payload: dict | None = None,
) -> DigitalTwinEdge:
    edge = DigitalTwinEdge(
        id=uuid4(),
        snapshot_id=snapshot_id,
        edge_key=edge_key,
        source_node_key=source,
        target_node_key=target,
        label=label,
        payload=payload or {},
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


def get_graph(db: Session, dpp_instance_id) -> dict | None:
    snapshot = get_snapshot_by_dpp(db, dpp_instance_id)
    if not snapshot:
        return None
    nodes = db.query(DigitalTwinNode).filter(DigitalTwinNode.snapshot_id == snapshot.id).all()
    edges = db.query(DigitalTwinEdge).filter(DigitalTwinEdge.snapshot_id == snapshot.id).all()
    return {"snapshot": snapshot, "nodes": nodes, "edges": edges}
