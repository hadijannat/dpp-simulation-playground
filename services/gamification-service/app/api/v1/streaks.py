from fastapi import APIRouter

router = APIRouter()

@router.get("/streaks")
def streaks():
    return {"items": []}
