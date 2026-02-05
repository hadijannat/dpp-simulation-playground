from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...dcat.catalog_builder import build_catalog
from ...models.asset import EdcAsset
from ...auth import require_roles

router = APIRouter()

@router.get("/catalog")
def get_catalog(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator", "consumer", "recycler"])
    assets = db.query(EdcAsset).all()
    items = []
    for asset in assets:
        items.append(
            {
                "id": asset.asset_id,
                "name": asset.name,
                "policy": asset.policy_odrl or {},
                "dataAddress": asset.data_address or {},
            }
        )
    return build_catalog(items)
