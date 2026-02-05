from fastapi import APIRouter

router = APIRouter()

@router.get("/participants")
def list_participants():
    return {"items": []}
