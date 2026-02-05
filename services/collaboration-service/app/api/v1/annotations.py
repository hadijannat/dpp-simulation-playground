from fastapi import APIRouter, Request
from ..schemas.annotation_schema import AnnotationCreate
from uuid import uuid4
from ...auth import require_roles

router = APIRouter()
_store = []

@router.get("/annotations")
def list_annotations(request: Request):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    return {"items": _store}

@router.post("/annotations")
def create_annotation(request: Request, payload: AnnotationCreate):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
