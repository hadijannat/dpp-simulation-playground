from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.participant import EdcParticipant
from ...auth import require_roles

router = APIRouter()

@router.get("/participants")
def list_participants(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    items = db.query(EdcParticipant).all()
    return {
        "items": [
            {"id": str(item.id), "participant_id": item.participant_id, "name": item.name, "metadata": item.metadata}
            for item in items
        ]
    }
