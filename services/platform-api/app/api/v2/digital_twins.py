from fastapi import APIRouter, Query, Request

from ...auth import require_roles
from ...config import PLATFORM_CORE_URL
from ...core.proxy import request_json
from ...schemas.v2 import DigitalTwinDiffResponse, DigitalTwinHistoryResponse, DigitalTwinResponse

router = APIRouter()


@router.get(
    "/digital-twins/{dpp_id}",
    response_model=DigitalTwinResponse,
    response_model_exclude_unset=True,
)
def get_digital_twin(request: Request, dpp_id: str):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return request_json(request, "GET", f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}")


@router.get(
    "/digital-twins/{dpp_id}/history",
    response_model=DigitalTwinHistoryResponse,
    response_model_exclude_unset=True,
)
def get_digital_twin_history(
    request: Request,
    dpp_id: str,
    limit: int = 25,
    offset: int = 0,
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return request_json(
        request,
        "GET",
        f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}/history",
        params={"limit": limit, "offset": offset},
    )


@router.get(
    "/digital-twins/{dpp_id}/diff",
    response_model=DigitalTwinDiffResponse,
    response_model_exclude_unset=True,
)
def get_digital_twin_diff(
    request: Request,
    dpp_id: str,
    from_snapshot: str = Query(..., alias="from"),
    to_snapshot: str = Query(..., alias="to"),
):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return request_json(
        request,
        "GET",
        f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}/diff",
        params={"from": from_snapshot, "to": to_snapshot},
    )
