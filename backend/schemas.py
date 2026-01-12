from pydantic import BaseModel
from typing import List

class Event(BaseModel):
    camera_id: str
    ts: str
    label: str
    confidence: float
    bbox: List[float]
