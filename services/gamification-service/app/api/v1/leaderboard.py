from fastapi import APIRouter

router = APIRouter()

@router.get("/leaderboard")
def leaderboard():
    return {"items": []}
