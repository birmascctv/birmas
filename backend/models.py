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

    # Raw YOLO outputs
    label = Column(String)          # YOLO class label
    bbox = Column(String)           # bounding box coordinates

    # Enriched product info
    product_brand = Column(String)
    product_name = Column(String)

    confidence = Column(Float)      # numeric confidence score

class Product(Base):
    __tablename__ = "product"

    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    product_brand = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
