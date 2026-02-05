from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class AasCreate(BaseModel):
    aas_identifier: str
    product_identifier: str | None = None
    product_name: str | None = None
    product_category: str | None = None
    session_id: Optional[str] = None


class AasValidateRequest(BaseModel):
    data: Dict[str, Any]
    templates: List[str] = []


class AasSubmodelCreate(BaseModel):
    submodel: Dict[str, Any]
    session_id: Optional[str] = None
    register: bool = True


class AasSubmodelElementsPatch(BaseModel):
    elements: Any


class AasxUploadRequest(BaseModel):
    filename: str
    content_base64: str
    session_id: Optional[str] = None
