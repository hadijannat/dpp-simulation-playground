from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4

from ...core.db import get_db
from ...models.asset import EdcAsset
from ...auth import require_roles

router = APIRouter()


class AssetCreate(BaseModel):
    asset_id: str
    name: str | None = None
    policy_odrl: dict | None = None
    data_address: dict | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    policy_odrl: dict | None = None
    data_address: dict | None = None


@router.get("/assets")
def list_assets(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    items = db.query(EdcAsset).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "asset_id": item.asset_id,
                "name": item.name,
                "policy_odrl": item.policy_odrl or {},
                "data_address": item.data_address or {},
            }
            for item in items
        ]
    }


@router.post("/assets")
def create_asset(request: Request, payload: AssetCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    existing = db.query(EdcAsset).filter(EdcAsset.asset_id == payload.asset_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Asset exists")
    item = EdcAsset(
        id=uuid4(),
        asset_id=payload.asset_id,
        name=payload.name,
        policy_odrl=payload.policy_odrl or {},
        data_address=payload.data_address or {},
    )
    db.add(item)
    db.commit()
    return {"id": str(item.id), "asset_id": item.asset_id, "name": item.name}


@router.patch("/assets/{asset_id}")
def update_asset(request: Request, asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcAsset).filter(EdcAsset.asset_id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if payload.name is not None:
        item.name = payload.name
    if payload.policy_odrl is not None:
        item.policy_odrl = payload.policy_odrl
    if payload.data_address is not None:
        item.data_address = payload.data_address
    db.commit()
    return {"id": str(item.id), "asset_id": item.asset_id, "name": item.name}
