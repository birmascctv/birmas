from pydantic import BaseModel
from typing import List

class Event(BaseModel):
    camera_id: str
    ts: str
    label: str
    confidence: float
    bbox: List[float]
    
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    user_id: int
    username: str

