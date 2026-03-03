from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# -------------------
# User Schemas
# -------------------
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    user_id: int

    class Config:
        orm_mode = True

# -------------------
# Event Schemas
# -------------------
class EventBase(BaseModel):
    camera_id: str
    ts: datetime
    label: str
    confidence: float
    bbox: str

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int

    class Config:
        orm_mode = True
