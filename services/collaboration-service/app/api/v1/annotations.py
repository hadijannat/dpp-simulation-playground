from fastapi import APIRouter
from ..schemas.annotation_schema import AnnotationCreate
from uuid import uuid4

router = APIRouter()
_store = []

@router.get("/annotations")
def list_annotations():
    return {"items": _store}

@router.post("/annotations")
def create_annotation(payload: AnnotationCreate):
    item = {"id": str(uuid4()), **payload.model_dump()}
    _store.append(item)
    return item
