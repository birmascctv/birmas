# from fastapi import APIRouter, Depends, HTTPException, Request
# from sqlalchemy.orm import Session
# from backend.db import SessionLocal
# from backend.models import Event, Product
# from backend.schemas import EventCreate, EventOut
# from datetime import datetime

# router = APIRouter()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @router.post("/events", response_model=EventOut)
# async def post_event(ev: EventCreate, request: Request, db: Session = Depends(get_db)):
#     try:
#         # Try to enrich product info based on YOLO label
#         product = db.query(Product).filter(Product.class_name == ev.label).first()

#         new_event = Event(
#             camera_id=ev.camera_id,
#             ts=ev.ts if ev.ts else datetime.utcnow(),
#             label=ev.label,
#             bbox=ev.bbox,
#             confidence=ev.confidence,
#             product_brand=product.product_brand if product else "Unknown",
#             product_name=product.product_name if product else "Unknown"
#         )
#         db.add(new_event)
#         db.commit()
#         db.refresh(new_event)

#         # Broadcast to WebSocket clients
#         manager = request.app.state.manager
#         await manager.broadcast(ev.model_dump())

#         return new_event
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/events", response_model=list[EventOut])
# async def get_events(camera_id: str, db: Session = Depends(get_db)):
#     try:
#         events = (
#             db.query(Event)
#             .filter(Event.camera_id == camera_id)
#             .order_by(Event.ts.desc())
#             .limit(100)
#             .all()
#         )
#         return events
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Event, Product
from datetime import datetime, timedelta

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/seed-events")
async def seed_events(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        if not products:
            raise HTTPException(status_code=400, detail="No products found in product table")

        # Generate 250 random events
        for _ in range(250):
            product = random.choice(products)
            ts = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))  # random time in last day
            confidence = round(random.uniform(0.5, 0.99), 2)
            bbox = f"{random.randint(0,300)},{random.randint(0,300)},{random.randint(300,640)},{random.randint(300,480)}"

            ev = Event(
                camera_id=random.choice(["cam1", "cam2", "cam3"]),
                ts=ts,
                label=product.class_name,       # raw YOLO label
                bbox=bbox,                      # fake bbox
                product_brand=product.product_brand,
                product_name=product.product_name,
                confidence=confidence
            )
            db.add(ev)

        db.commit()
        return {"status": "ok", "inserted": 250}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
