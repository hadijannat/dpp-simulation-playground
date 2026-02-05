from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from services.shared.repositories import digital_twin_repo

router = APIRouter()


@router.get("/core/digital-twins/{dpp_id}")
def get_digital_twin(request: Request, dpp_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    graph = digital_twin_repo.get_graph(db, dpp_id)
    if not graph:
        # Fallback: return empty graph structure
        return {
            "dpp_id": dpp_id,
            "nodes": [],
            "edges": [],
            "timeline": [],
        }
    return {
        "dpp_id": dpp_id,
        "nodes": [
            {"id": n.node_key, "label": n.label, "type": n.node_type, "payload": n.payload or {}}
            for n in graph["nodes"]
        ],
        "edges": [
            {"id": e.edge_key, "source": e.source_node_key, "target": e.target_node_key, "label": e.label or ""}
            for e in graph["edges"]
        ],
        "timeline": [],
    }
