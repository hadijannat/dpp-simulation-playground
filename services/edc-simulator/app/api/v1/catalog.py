from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...dcat.catalog_builder import build_catalog
from ...models.asset import EdcAsset
from ...models.participant import EdcParticipant
from ...auth import require_roles

router = APIRouter()

@router.get("/catalog")
def get_catalog(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator", "consumer", "recycler"])
    assets = db.query(EdcAsset).all()
    participants = {item.participant_id: item for item in db.query(EdcParticipant).all()}
    items = []
    for asset in assets:
        data_address = asset.data_address or {}
        provider_id = data_address.get("provider_id")
        provider = participants.get(provider_id) if provider_id else None
        items.append(
            {
                "id": asset.asset_id,
                "name": asset.name,
                "title": asset.name,
                "description": data_address.get("description"),
                "keywords": data_address.get("keywords") or [],
                "publisher": {
                    "id": provider_id,
                    "name": provider.name if provider else provider_id,
                },
                "policy": asset.policy_odrl or {},
                "dataAddress": data_address,
            }
        )
    return build_catalog(items)
