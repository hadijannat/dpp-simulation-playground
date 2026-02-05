from fastapi import APIRouter
from ...engine.achievement_engine import load_achievements

router = APIRouter()

@router.get("/achievements")
def list_achievements():
    return {"items": load_achievements()}
