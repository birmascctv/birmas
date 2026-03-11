import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Event, Product, now_wib
from backend.schemas import EventCreate, EventOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/events", response_model=EventOut)
async def post_event(ev: EventCreate, request: Request, db: Session = 
    Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.class_name ==
            ev.label).first()

        new_event = Event(
            camera_id     = ev.camera_id,
        ts            = ev.ts.replace(tzinfo=None) if ev.ts else now_wib(),
            label         = ev.label,
            bbox          = ev.bbox,
            confidence    = ev.confidence,
            event_type    = ev.event_type or "added",
            product_brand = product.product_brand if product else "Unknown",
            product_name  = product.product_name  if product else "Unknown",
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        manager = request.app.state.manager
        await manager.broadcast({
            "id":            new_event.id,
            "camera_id":     new_event.camera_id,
            "ts":            new_event.ts.isoformat(),
            "label":         new_event.label,
            "bbox":          new_event.bbox,
            "confidence":    new_event.confidence,
            "event_type":    new_event.event_type,
            "product_brand": new_event.product_brand,
            "product_name":  new_event.product_name,
        })
        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=list[EventOut])
async def get_events(
    camera_id:  str | None = None,
    start_date: str | None = None,
    end_date:     str | None = None,
    event_type:   str | None = None,
    product_name: str | None = None,
    limit:        int = 500,
    db: Session = Depends(get_db)
):
    q = db.query(Event)
    if camera_id:
        q = q.filter(Event.camera_id == camera_id)
    if start_date:
        q = q.filter(Event.ts >= start_date)
    if end_date:
        q = q.filter(Event.ts <= end_date)
    if event_type:
        q = q.filter(Event.event_type == event_type)
    if product_name:
        q = q.filter(Event.product_name == product_name)
    return q.order_by(Event.ts.desc()).limit(min(limit, 5000)).all()


@router.get("/camera-status")
async def camera_status():
    try:
        r = httpx.get("http://localhost:9997/v3/paths/list", timeout=2)
        items = r.json().get("items", [])
        cameras = [{"id": it["name"], "online": bool(it.get("source"))} for it in items]
        return {"cameras": cameras}
    except Exception:
        return {"cameras": []}

@router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    """Return all products from the product table."""
    from backend.models import Product
    products = db.query(Product).order_by(Product.product_brand, Product.product_name).all()
    return [
        {
            "class_id":      p.class_id,
            "class_name":    p.class_name,
            "product_brand": p.product_brand,
            "product_name":  p.product_name,
        }
        for p in products
    ]
