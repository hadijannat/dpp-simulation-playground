from pydantic import BaseModel
from typing import Dict, Any


class GenericResponse(BaseModel):
    status: str
    data: Dict[str, Any] | None = None
