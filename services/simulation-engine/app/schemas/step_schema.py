from pydantic import BaseModel, Field
from typing import Dict, Any


class StepExecuteRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
