from pydantic import BaseModel
from typing import Optional, Dict, Any


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    role: str
    state: Optional[Dict] = None
    lifecycle_state: Optional[str] = None


class SessionUpdate(BaseModel):
    role: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    lifecycle_state: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    role: str
    state: Dict
    lifecycle_state: Optional[str] = None
    is_active: bool = True
