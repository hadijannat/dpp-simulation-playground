from fastapi import APIRouter, Request, Depends
from ...schemas.annotation_schema import AnnotationCreate
from uuid import uuid4
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.annotation import Annotation
from ...auth import require_roles

router = APIRouter()

@router.get("/annotations")
def list_annotations(
    request: Request,
    story_id: int | None = None,
    status: str | None = None,
    target_element: str | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "regulator", "manufacturer"])
    query = db.query(Annotation)
    if story_id is not None:
        query = query.filter(Annotation.story_id == story_id)
    if status:
        query = query.filter(Annotation.status == status)
    if target_element:
        query = query.filter(Annotation.target_element == target_element)
    items = query.order_by(Annotation.created_at.desc()).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "story_id": item.story_id,
                "target_element": item.target_element,
                "annotation_type": item.annotation_type,
                "content": item.content,
                "status": item.status,
                "votes_count": item.votes_count,
            }
            for item in items
        ]
    }

@router.post("/annotations")
def create_annotation(request: Request, payload: AnnotationCreate, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "regulator", "consumer", "recycler"])
    item = Annotation(
        id=uuid4(),
        user_id=request.state.user.get("sub"),
        story_id=payload.story_id,
        target_element=payload.target_element,
        annotation_type=payload.annotation_type,
        content=payload.content,
        status="open",
    )
    db.add(item)
    db.commit()
    return {
        "id": str(item.id),
        "story_id": item.story_id,
        "target_element": item.target_element,
        "annotation_type": item.annotation_type,
        "content": item.content,
        "status": item.status,
    }
