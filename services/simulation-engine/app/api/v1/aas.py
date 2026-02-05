from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from ...schemas.aas_schema import AasCreate, AasValidateRequest
from ...core.db import get_db
from ...config import BASYX_BASE_URL, AAS_REGISTRY_URL, SUBMODEL_REGISTRY_URL
from ...aas.basyx_client import BasyxClient
from ...models.dpp_instance import DppInstance
from ...models.validation_result import ValidationResult
from pathlib import Path
import os
from ...auth import require_roles

router = APIRouter()

@router.post("/aas/shells")
def create_shell(request: Request, payload: AasCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    client = BasyxClient(base_url=BASYX_BASE_URL)
    shell_payload = {
        "id": payload.aas_identifier,
        "idShort": payload.product_name or "dpp-asset",
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": payload.product_identifier or payload.aas_identifier,
        },
    }
    status = "created"
    try:
        shell = client.create_shell(shell_payload)
    except Exception as exc:
        shell = {"error": str(exc), "payload": shell_payload}
        status = "degraded"
    if AAS_REGISTRY_URL:
        try:
            client.register_shell_descriptor(AAS_REGISTRY_URL, shell_payload)
        except Exception:
            pass
    dpp = DppInstance(
        id=uuid4(),
        session_id=payload.session_id,
        aas_identifier=payload.aas_identifier,
        product_identifier=payload.product_identifier,
        product_name=payload.product_name,
        product_category=payload.product_category,
        compliance_status={},
    )
    try:
        db.add(dpp)
        db.commit()
    except Exception:
        db.rollback()
    return {"status": status, "aas": shell}

@router.get("/aas/shells")
def list_shells(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    client = BasyxClient(base_url=BASYX_BASE_URL)
    try:
        return client.list_shells()
    except Exception as exc:
        return {"items": [], "error": str(exc)}

@router.post("/aas/validate")
def validate_aas(request: Request, payload: AasValidateRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    candidate_dirs = []
    env_dir = os.getenv("IDTA_TEMPLATES_DIR")
    if env_dir:
        candidate_dirs.append(Path(env_dir))
    candidate_dirs.extend(
        [
            Path(__file__).resolve().parents[5] / "data" / "idta-templates",
            Path(__file__).resolve().parents[3] / "data" / "idta-templates",
        ]
    )
    templates_dir = next((p for p in candidate_dirs if p.exists()), candidate_dirs[-1])
    missing_templates = []
    for template in payload.templates:
        if not (templates_dir / template).exists():
            missing_templates.append(template)
    status = "ok" if not missing_templates else "missing_templates"
    result = {"status": status, "missing_templates": missing_templates}
    record = ValidationResult(id=str(uuid4()), result=result)
    db.add(record)
    db.commit()
    return result
