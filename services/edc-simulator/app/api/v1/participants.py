from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.participant import EdcParticipant
from ...auth import require_roles

router = APIRouter()


class ParticipantCreate(BaseModel):
    participant_id: str
    name: str | None = None
    metadata: dict | None = None


class ParticipantUpdate(BaseModel):
    name: str | None = None
    metadata: dict | None = None


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


@router.post("/participants")
def create_participant(request: Request, payload: ParticipantCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    existing = db.query(EdcParticipant).filter(EdcParticipant.participant_id == payload.participant_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Participant exists")
    item = EdcParticipant(
        id=uuid4(),
        participant_id=payload.participant_id,
        name=payload.name,
        metadata=payload.metadata or {},
    )
    db.add(item)
    db.commit()
    return {"id": str(item.id), "participant_id": item.participant_id, "name": item.name}


@router.patch("/participants/{participant_id}")
def update_participant(request: Request, participant_id: str, payload: ParticipantUpdate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    item = db.query(EdcParticipant).filter(EdcParticipant.participant_id == participant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if payload.name is not None:
        item.name = payload.name
    if payload.metadata is not None:
        item.metadata = payload.metadata
    db.commit()
    return {"id": str(item.id), "participant_id": item.participant_id, "name": item.name}
