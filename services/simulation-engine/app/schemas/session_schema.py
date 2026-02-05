from pydantic import BaseModel
from typing import Optional, Dict, Any


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    role: str
    state: Optional[Dict] = None


class SessionUpdate(BaseModel):
    role: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    role: str
    state: Dict
