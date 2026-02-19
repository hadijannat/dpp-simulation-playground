from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.digital_twin_snapshot import DigitalTwinSnapshot
from ..models.digital_twin_node import DigitalTwinNode
from ..models.digital_twin_edge import DigitalTwinEdge


def get_snapshot_by_dpp(db: Session, dpp_instance_id) -> DigitalTwinSnapshot | None:
    return (
        db.query(DigitalTwinSnapshot)
        .filter(DigitalTwinSnapshot.dpp_instance_id == dpp_instance_id)
        .order_by(DigitalTwinSnapshot.created_at.desc(), DigitalTwinSnapshot.id.desc())
        .first()
    )


def list_snapshots(
    db: Session,
    dpp_instance_id,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DigitalTwinSnapshot], int]:
    query = db.query(DigitalTwinSnapshot).filter(
        DigitalTwinSnapshot.dpp_instance_id == dpp_instance_id
    )
    total = query.count()
    items = (
        query.order_by(
            DigitalTwinSnapshot.created_at.desc(), DigitalTwinSnapshot.id.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_snapshot_by_id(
    db: Session, dpp_instance_id, snapshot_id
) -> DigitalTwinSnapshot | None:
    return (
        db.query(DigitalTwinSnapshot)
        .filter(
            DigitalTwinSnapshot.dpp_instance_id == dpp_instance_id,
            DigitalTwinSnapshot.id == snapshot_id,
        )
        .first()
    )


def create_snapshot(
    db: Session,
    dpp_instance_id,
    label: str | None = None,
    metadata: dict | None = None,
) -> DigitalTwinSnapshot:
    snapshot = DigitalTwinSnapshot(
        id=uuid4(),
        dpp_instance_id=dpp_instance_id,
        label=label,
        metadata_=metadata or {},
    )
    db.add(snapshot)
    db.flush()
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
    db.flush()
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
    db.flush()
    db.refresh(edge)
    return edge


def get_graph_for_snapshot(db: Session, snapshot_id) -> dict[str, Any]:
    nodes = (
        db.query(DigitalTwinNode)
        .filter(DigitalTwinNode.snapshot_id == snapshot_id)
        .order_by(DigitalTwinNode.node_key.asc())
        .all()
    )
    edges = (
        db.query(DigitalTwinEdge)
        .filter(DigitalTwinEdge.snapshot_id == snapshot_id)
        .order_by(DigitalTwinEdge.edge_key.asc())
        .all()
    )
    return {"nodes": nodes, "edges": edges}


def get_graph(db: Session, dpp_instance_id) -> dict | None:
    snapshot = get_snapshot_by_dpp(db, dpp_instance_id)
    if not snapshot:
        return None
    graph = get_graph_for_snapshot(db, snapshot.id)
    return {"snapshot": snapshot, "nodes": graph["nodes"], "edges": graph["edges"]}


def get_snapshot_counts(
    db: Session, snapshot_ids: list[Any]
) -> tuple[dict[Any, int], dict[Any, int]]:
    if not snapshot_ids:
        return {}, {}

    node_counts = dict(
        db.query(DigitalTwinNode.snapshot_id, func.count(DigitalTwinNode.id))
        .filter(DigitalTwinNode.snapshot_id.in_(snapshot_ids))
        .group_by(DigitalTwinNode.snapshot_id)
        .all()
    )
    edge_counts = dict(
        db.query(DigitalTwinEdge.snapshot_id, func.count(DigitalTwinEdge.id))
        .filter(DigitalTwinEdge.snapshot_id.in_(snapshot_ids))
        .group_by(DigitalTwinEdge.snapshot_id)
        .all()
    )
    return node_counts, edge_counts


def _node_to_dict(node: DigitalTwinNode) -> dict[str, Any]:
    return {
        "id": node.node_key,
        "type": node.node_type,
        "label": node.label,
        "payload": node.payload or {},
    }


def _edge_to_dict(edge: DigitalTwinEdge) -> dict[str, Any]:
    return {
        "id": edge.edge_key,
        "source": edge.source_node_key,
        "target": edge.target_node_key,
        "label": edge.label or "",
        "payload": edge.payload or {},
    }


def format_graph_payload(
    dpp_id: str,
    snapshot: DigitalTwinSnapshot,
    nodes: list[DigitalTwinNode],
    edges: list[DigitalTwinEdge],
) -> dict:
    return {
        "dpp_id": dpp_id,
        "snapshot_id": str(snapshot.id),
        "snapshot_label": snapshot.label,
        "snapshot_created_at": snapshot.created_at.isoformat()
        if snapshot.created_at
        else None,
        "snapshot_metadata": snapshot.metadata_ or {},
        "nodes": [_node_to_dict(node) for node in nodes],
        "edges": [_edge_to_dict(edge) for edge in edges],
    }


def _clone_graph_into_snapshot(
    db: Session,
    *,
    snapshot_id,
    base_nodes: list[DigitalTwinNode],
    base_edges: list[DigitalTwinEdge],
) -> tuple[list[DigitalTwinNode], list[DigitalTwinEdge]]:
    cloned_nodes: list[DigitalTwinNode] = []
    for node in base_nodes:
        clone = DigitalTwinNode(
            id=uuid4(),
            snapshot_id=snapshot_id,
            node_key=node.node_key,
            node_type=node.node_type,
            label=node.label,
            payload=deepcopy(node.payload or {}),
        )
        db.add(clone)
        cloned_nodes.append(clone)

    cloned_edges: list[DigitalTwinEdge] = []
    for edge in base_edges:
        clone = DigitalTwinEdge(
            id=uuid4(),
            snapshot_id=snapshot_id,
            edge_key=edge.edge_key,
            source_node_key=edge.source_node_key,
            target_node_key=edge.target_node_key,
            label=edge.label,
            payload=deepcopy(edge.payload or {}),
        )
        db.add(clone)
        cloned_edges.append(clone)

    return cloned_nodes, cloned_edges


def _seed_default_graph(
    db: Session, snapshot_id, dpp_instance
) -> tuple[list[DigitalTwinNode], list[DigitalTwinEdge]]:
    product_payload = {
        "aas_identifier": getattr(dpp_instance, "aas_identifier", None),
        "product_identifier": getattr(dpp_instance, "product_identifier", None),
        "product_category": getattr(dpp_instance, "product_category", None),
    }
    nodes = [
        DigitalTwinNode(
            id=uuid4(),
            snapshot_id=snapshot_id,
            node_key="product",
            node_type="asset",
            label=getattr(dpp_instance, "product_name", None) or "Product",
            payload=product_payload,
        ),
        DigitalTwinNode(
            id=uuid4(),
            snapshot_id=snapshot_id,
            node_key="compliance",
            node_type="status",
            label="Compliance",
            payload={"status": "pending"},
        ),
        DigitalTwinNode(
            id=uuid4(),
            snapshot_id=snapshot_id,
            node_key="transfer",
            node_type="dataspace",
            label="Transfer",
            payload={},
        ),
    ]
    for node in nodes:
        db.add(node)

    edges = [
        DigitalTwinEdge(
            id=uuid4(),
            snapshot_id=snapshot_id,
            edge_key="product-compliance",
            source_node_key="product",
            target_node_key="compliance",
            label="validates",
            payload={},
        ),
        DigitalTwinEdge(
            id=uuid4(),
            snapshot_id=snapshot_id,
            edge_key="product-transfer",
            source_node_key="product",
            target_node_key="transfer",
            label="transfers",
            payload={},
        ),
    ]
    for edge in edges:
        db.add(edge)

    return nodes, edges


def capture_snapshot_for_dpp(
    db: Session,
    *,
    dpp_instance,
    label: str | None = None,
    metadata: dict[str, Any] | None = None,
    session_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_graph = get_graph(db, dpp_instance.id)

    snapshot = DigitalTwinSnapshot(
        id=uuid4(),
        dpp_instance_id=dpp_instance.id,
        label=label,
        metadata_=metadata or {},
    )
    db.add(snapshot)
    db.flush()

    if base_graph:
        nodes, edges = _clone_graph_into_snapshot(
            db,
            snapshot_id=snapshot.id,
            base_nodes=base_graph["nodes"],
            base_edges=base_graph["edges"],
        )
    else:
        nodes, edges = _seed_default_graph(db, snapshot.id, dpp_instance)

    node_map = {node.node_key: node for node in nodes}

    product = node_map.get("product")
    if product:
        payload = dict(product.payload or {})
        payload.update(
            {
                "aas_identifier": getattr(dpp_instance, "aas_identifier", None),
                "product_identifier": getattr(dpp_instance, "product_identifier", None),
                "product_category": getattr(dpp_instance, "product_category", None),
            }
        )
        product.payload = payload
        if getattr(dpp_instance, "product_name", None):
            product.label = dpp_instance.product_name

    state = session_state or {}
    compliance = node_map.get("compliance")
    if compliance:
        compliance_payload = dict(compliance.payload or {})
        status = None
        summary = None
        compliance_result = state.get("last_validation")
        if isinstance(compliance_result, dict):
            status = compliance_result.get("status")
            if isinstance(compliance_result.get("data"), dict):
                status = status or compliance_result["data"].get("status")
                summary = compliance_result["data"].get("summary")
        dpp_compliance = getattr(dpp_instance, "compliance_status", None)
        if isinstance(dpp_compliance, dict):
            status = status or dpp_compliance.get("status")
            summary = summary or dpp_compliance.get("summary")
        if status:
            compliance_payload["status"] = status
        if summary is not None:
            compliance_payload["summary"] = summary
        compliance.payload = compliance_payload

    transfer = node_map.get("transfer")
    if transfer:
        transfer_payload = dict(transfer.payload or {})
        edc_state = state.get("edc_state")
        if isinstance(edc_state, dict):
            transfer_payload.update(
                {
                    "status": edc_state.get("status"),
                    "details": edc_state.get("data")
                    if isinstance(edc_state.get("data"), dict)
                    else edc_state,
                }
            )
        transfer.payload = transfer_payload

    db.flush()
    db.refresh(snapshot)
    return {"snapshot": snapshot, "nodes": nodes, "edges": edges}


def build_diff(from_graph: dict[str, Any], to_graph: dict[str, Any]) -> dict[str, Any]:
    def _node_keyed(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {node["id"]: node for node in graph.get("nodes", [])}

    def _edge_keyed(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {edge["id"]: edge for edge in graph.get("edges", [])}

    from_nodes = _node_keyed(from_graph)
    to_nodes = _node_keyed(to_graph)
    from_edges = _edge_keyed(from_graph)
    to_edges = _edge_keyed(to_graph)

    def _added_removed_changed(
        before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
    ):
        before_keys = set(before.keys())
        after_keys = set(after.keys())
        added = [after[key] for key in sorted(after_keys - before_keys)]
        removed = [before[key] for key in sorted(before_keys - after_keys)]
        changed = []
        for key in sorted(before_keys & after_keys):
            if before[key] != after[key]:
                changed.append({"key": key, "before": before[key], "after": after[key]})
        return {"added": added, "removed": removed, "changed": changed}

    node_diff = _added_removed_changed(from_nodes, to_nodes)
    edge_diff = _added_removed_changed(from_edges, to_edges)

    summary = {
        "nodes_added": len(node_diff["added"]),
        "nodes_removed": len(node_diff["removed"]),
        "nodes_changed": len(node_diff["changed"]),
        "edges_added": len(edge_diff["added"]),
        "edges_removed": len(edge_diff["removed"]),
        "edges_changed": len(edge_diff["changed"]),
    }
    return {
        "summary": summary,
        "nodes": node_diff,
        "edges": edge_diff,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
