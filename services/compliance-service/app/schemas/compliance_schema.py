from pydantic import BaseModel
from typing import List, Dict, Any


class ComplianceCheckRequest(BaseModel):
    data: Dict[str, Any]
    regulations: List[str]
    user_id: str | None = None
    session_id: str | None = None
    story_code: str | None = None
