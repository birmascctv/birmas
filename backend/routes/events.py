from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Event
from backend.schemas import EventCreate, EventOut
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/events", response_model=EventOut)
async def post_event(ev: EventCreate, request: Request, db: Session = Depends(get_db)):
    try:
        new_event = Event(
            camera_id=ev.camera_id,
            ts=ev.ts if ev.ts else datetime.utcnow(),  # default to now if not provided
            product_brand=ev.product_brand,
            product_name=ev.product_name,
            confidence=ev.confidence
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        # Broadcast to WebSocket clients
        manager = request.app.state.manager
        await manager.broadcast(ev.model_dump())

        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=list[EventOut])
async def get_events(camera_id: str, db: Session = Depends(get_db)):
    try:
        events = (
            db.query(Event)
            .filter(Event.camera_id == camera_id)
            .order_by(Event.ts.desc())
            .limit(100)
            .all()
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
