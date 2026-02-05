from pydantic import BaseModel
from typing import Dict, Any


class StepExecuteRequest(BaseModel):
    payload: Dict[str, Any] = {}
