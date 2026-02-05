from fastapi import APIRouter, Request
from ...dcat.catalog_builder import build_catalog
from ...auth import require_roles

router = APIRouter()

@router.get("/catalog")
def get_catalog(request: Request):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator", "consumer", "recycler"])
    assets = []
    return build_catalog(assets)
