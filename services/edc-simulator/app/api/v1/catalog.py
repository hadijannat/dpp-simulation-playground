from fastapi import APIRouter
from ...dcat.catalog_builder import build_catalog

router = APIRouter()

@router.get("/catalog")
def get_catalog():
    assets = []
    return build_catalog(assets)
