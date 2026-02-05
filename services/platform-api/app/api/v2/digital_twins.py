from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import PLATFORM_CORE_URL
from ...core.proxy import request_json

router = APIRouter()


@router.get("/digital-twins/{dpp_id}")
def get_digital_twin(request: Request, dpp_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}")
