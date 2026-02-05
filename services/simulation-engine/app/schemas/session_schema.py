from pydantic import BaseModel
from typing import Optional, Dict


class SessionCreate(BaseModel):
    user_id: str
    role: str
    state: Optional[Dict] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    role: str
    state: Dict
