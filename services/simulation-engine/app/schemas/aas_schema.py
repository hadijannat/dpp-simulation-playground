from pydantic import BaseModel


class AasCreate(BaseModel):
    aas_identifier: str
    product_name: str | None = None
    product_category: str | None = None
