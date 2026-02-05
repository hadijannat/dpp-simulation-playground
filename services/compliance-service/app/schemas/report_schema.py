from pydantic import BaseModel
from typing import List, Dict, Any


class ComplianceReport(BaseModel):
    status: str
    violations: List[Dict[str, Any]]
