from sqlalchemy import Column, Integer, String, DateTime, Float
from backend.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    camera_id = Column(String, index=True)
    product_brand = Column(String)
    product_name = Column(String)
    confidence = Column(Float)   # store numeric confidence scores
