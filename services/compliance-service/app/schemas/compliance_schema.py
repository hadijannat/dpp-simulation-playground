from pydantic import BaseModel
from typing import List, Dict, Any


class ComplianceCheckRequest(BaseModel):
    data: Dict[str, Any]
    regulations: List[str]
