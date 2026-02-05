from fastapi import APIRouter, Request

from ...auth import require_roles
from ...schemas.v2 import DigitalTwinResponse

router = APIRouter()


@router.get("/digital-twins/{dpp_id}", response_model=DigitalTwinResponse)
def get_digital_twin(request: Request, dpp_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return {
        "dpp_id": dpp_id,
        "nodes": [
            {"id": "product", "label": "Product", "type": "asset"},
            {"id": "compliance", "label": "Compliance", "type": "status"},
            {"id": "transfer", "label": "Transfer", "type": "dataspace"},
        ],
        "edges": [
            {"id": "product-compliance", "source": "product", "target": "compliance"},
            {"id": "compliance-transfer", "source": "compliance", "target": "transfer"},
        ],
        "timeline": [],
    }
