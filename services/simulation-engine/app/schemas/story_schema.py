from pydantic import BaseModel
from typing import List, Dict


class Story(BaseModel):
    code: str
    title: str
    steps: List[Dict]
