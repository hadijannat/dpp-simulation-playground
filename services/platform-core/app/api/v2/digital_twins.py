from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from services.shared.repositories import digital_twin_repo

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}: '{value}'") from exc


def _serialize_snapshot(snapshot, node_count: int = 0, edge_count: int = 0) -> dict:
    return {
        "snapshot_id": str(snapshot.id),
        "label": snapshot.label,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
        "metadata": snapshot.metadata_ or {},
        "node_count": node_count,
        "edge_count": edge_count,
    }


@router.get("/core/digital-twins/{dpp_id}")
def get_digital_twin(request: Request, dpp_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ALL_ROLES)
    dpp_uuid = _parse_uuid(dpp_id, "dpp_id")
    graph = digital_twin_repo.get_graph(db, dpp_uuid)
    if not graph:
        return {
            "dpp_id": dpp_id,
            "nodes": [],
            "edges": [],
            "timeline": [],
        }
    payload = digital_twin_repo.format_graph_payload(dpp_id, graph["snapshot"], graph["nodes"], graph["edges"])
    payload["timeline"] = []
    return payload


@router.get("/core/digital-twins/{dpp_id}/history")
def get_digital_twin_history(
    request: Request,
    dpp_id: str,
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)
    dpp_uuid = _parse_uuid(dpp_id, "dpp_id")
    bounded_limit = max(1, min(limit, 200))
    bounded_offset = max(0, offset)

    items, total = digital_twin_repo.list_snapshots(
        db,
        dpp_uuid,
        limit=bounded_limit,
        offset=bounded_offset,
    )
    snapshot_ids = [item.id for item in items]
    node_counts, edge_counts = digital_twin_repo.get_snapshot_counts(db, snapshot_ids)

    return {
        "dpp_id": dpp_id,
        "items": [
            _serialize_snapshot(
                snapshot,
                node_count=node_counts.get(snapshot.id, 0),
                edge_count=edge_counts.get(snapshot.id, 0),
            )
            for snapshot in items
        ],
        "total": total,
        "limit": bounded_limit,
        "offset": bounded_offset,
    }


@router.get("/core/digital-twins/{dpp_id}/diff")
def get_digital_twin_diff(
    request: Request,
    dpp_id: str,
    from_snapshot: str = Query(..., alias="from"),
    to_snapshot: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)
    dpp_uuid = _parse_uuid(dpp_id, "dpp_id")
    from_snapshot_uuid = _parse_uuid(from_snapshot, "from")
    to_snapshot_uuid = _parse_uuid(to_snapshot, "to")

    from_item = digital_twin_repo.get_snapshot_by_id(db, dpp_uuid, from_snapshot_uuid)
    to_item = digital_twin_repo.get_snapshot_by_id(db, dpp_uuid, to_snapshot_uuid)
    if not from_item or not to_item:
        raise HTTPException(status_code=404, detail="One or both snapshots were not found for this dpp_id")

    from_graph_data = digital_twin_repo.get_graph_for_snapshot(db, from_item.id)
    to_graph_data = digital_twin_repo.get_graph_for_snapshot(db, to_item.id)

    from_graph = digital_twin_repo.format_graph_payload(
        dpp_id,
        from_item,
        from_graph_data["nodes"],
        from_graph_data["edges"],
    )
    to_graph = digital_twin_repo.format_graph_payload(
        dpp_id,
        to_item,
        to_graph_data["nodes"],
        to_graph_data["edges"],
    )

    return {
        "dpp_id": dpp_id,
        "from_snapshot": _serialize_snapshot(
            from_item,
            node_count=len(from_graph_data["nodes"]),
            edge_count=len(from_graph_data["edges"]),
        ),
        "to_snapshot": _serialize_snapshot(
            to_item,
            node_count=len(to_graph_data["nodes"]),
            edge_count=len(to_graph_data["edges"]),
        ),
        "diff": digital_twin_repo.build_diff(from_graph, to_graph),
    }
