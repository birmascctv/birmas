from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Event, Product
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
        # Try to enrich product info based on YOLO label
        product = db.query(Product).filter(Product.class_name == ev.label).first()

        new_event = Event(
            camera_id=ev.camera_id,
            ts=ev.ts if ev.ts else datetime.utcnow(),
            label=ev.label,
            bbox=ev.bbox,
            confidence=ev.confidence,
            product_brand=product.product_brand if product else "Unknown",
            product_name=product.product_name if product else "Unknown"
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        # Broadcast to WebSocket clients
        manager = request.app.state.manager
        await manager.broadcast({
            "id": new_event.id,
            "camera_id": new_event.camera_id,
            "ts": new_event.ts.isoformat(),
            "label": new_event.label,
            "bbox": new_event.bbox,
            "confidence": new_event.confidence,
            "product_brand": new_event.product_brand,
            "product_name": new_event.product_name,
        })
        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=list[EventOut])
async def get_events(
    camera_id: str | None = None,
    start_date: str | None = None,
    db: Session = Depends(get_db)
):
    q = db.query(Event)
    if camera_id:
        q = q.filter(Event.camera_id == camera_id)
    if start_date:
        q = q.filter(Event.ts >= start_date)
    return q.order_by(Event.ts.desc()).limit(500).all()