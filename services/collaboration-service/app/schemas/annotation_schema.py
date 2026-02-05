from pydantic import BaseModel

class AnnotationCreate(BaseModel):
    story_id: int | None = None
    content: str
    annotation_type: str = "note"
