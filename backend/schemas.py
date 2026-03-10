from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class EventCreate(BaseModel):
    camera_id:  str
    ts:         Optional[datetime] = None
    label:      str
    bbox:       str
    confidence: float
    event_type: Optional[str] = "added"   # "added" | "restock" | "sold"

class EventBase(BaseModel):
    camera_id:    str
    ts:           datetime
    label:        str
    bbox:         str
    product_brand: str
    product_name:  str
    confidence:   float
    event_type:   str

class EventOut(EventBase):
    id: int
    class Config:
        from_attributes = True