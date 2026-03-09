from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.db import SessionLocal
from backend.models import Event

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats/counts")
def get_counts(camera_id: str, interval: str = "hour", db: Session = Depends(get_db)):
    rows = (
        db.query(func.date_trunc(interval, Event.ts).label("bucket"), func.count())
        .filter(Event.camera_id == camera_id)
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )
    return {
        "labels": [r[0].isoformat() for r in rows],
        "counts": [r[1] for r in rows]
    }
