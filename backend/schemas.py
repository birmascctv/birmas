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
    id: int

    class Config:
        from_attributes = True

# -------------------
# Event Schemas
# -------------------
class EventBase(BaseModel):
    camera_id: str
    ts: datetime
    label: str
    bbox: str
    product_brand: str
    product_name: str
    confidence: float

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int

    class Config:
        from_attributes = True
