from sqlalchemy import Column, Integer, String, DateTime, Float
from backend.db import Base
from datetime import datetime, timezone, timedelta

# Jakarta timezone (WIB = UTC+7) — used as default for timestamps
WIB = timezone(timedelta(hours=7))

def now_wib():
    """Current naive datetime in Jakarta local time (WIB)."""
    return datetime.now(WIB).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Event(Base):
    __tablename__ = "events"
    id            = Column(Integer, primary_key=True, index=True,
        autoincrement=True)
    ts            = Column(DateTime, default=now_wib, index=True)  # stored as naive WIB (Jakarta local time)
    camera_id     = Column(String, index=True)
    label         = Column(String)
    bbox          = Column(String)
    product_brand = Column(String)
    product_name  = Column(String)
    confidence    = Column(Float)
    event_type    = Column(String, default="added")  # "added" | "restock" | "sold" | "missing"

class Product(Base):
    __tablename__ = "product"
    class_id      = Column(Integer, primary_key=True, index=True)
    class_name    = Column(String, nullable=False)
    product_brand = Column(String, nullable=False)
    product_name  = Column(String, nullable=False)

class PeopleEvent(Base):
    """
    A person crossing the door (in/out) or a periodic activity heartbeat
    used to infer whether the store currently has customers/staff activity.
    event_type: "in" | "out" | "activity"
      - "in"/"out": a person's track originated at / ended at the door zone.
      - "activity": periodic heartbeat posted whenever >=1 person is visible
        anywhere in frame, throttled to one per ACTIVITY_BUCKET_SECONDS, used
        to build the hourly foot-traffic/occupancy chart and the
        store-open/closed indicator.
    """
    __tablename__ = "people_events"
    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ts         = Column(DateTime, default=now_wib, index=True)
    camera_id  = Column(String, index=True)
    event_type = Column(String, index=True)  # "in" | "out" | "activity"
    confidence = Column(Float, default=0.0)