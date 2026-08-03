from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import timedelta
from backend.db import SessionLocal
from backend.models import PeopleEvent, now_wib
from backend.schemas import PeopleEventCreate, PeopleEventOut

router = APIRouter()

# How recently an "activity" heartbeat must have been posted for the store
# to be considered currently "open"/active. Must be a bit larger than the
# Pi's ACTIVITY_BUCKET_SECONDS so a normal gap between heartbeats doesn't
# flap the status.
STORE_ACTIVE_WINDOW_MIN = 10


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/people-events", response_model=PeopleEventOut)
async def post_people_event(ev: PeopleEventCreate, request: Request,
                             db: Session = Depends(get_db)):
    try:
        new_event = PeopleEvent(
            camera_id  = ev.camera_id,
            ts         = ev.ts.replace(tzinfo=None) if ev.ts else now_wib(),
            event_type = ev.event_type,
            confidence = ev.confidence,
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        manager = request.app.state.manager
        await manager.broadcast({
            "kind":       "people_event",
            "id":         new_event.id,
            "camera_id":  new_event.camera_id,
            "ts":         new_event.ts.isoformat(),
            "event_type": new_event.event_type,
            "confidence": new_event.confidence,
        })
        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/people-events", response_model=list[PeopleEventOut])
async def get_people_events(
    camera_id:  str | None = None,
    start_date: str | None = None,
    end_date:   str | None = None,
    event_type: str | None = None,
    limit:      int = 2000,
    db: Session = Depends(get_db),
):
    q = db.query(PeopleEvent)
    if camera_id:
        q = q.filter(PeopleEvent.camera_id == camera_id)
    if start_date:
        q = q.filter(PeopleEvent.ts >= start_date)
    if end_date:
        q = q.filter(PeopleEvent.ts <= end_date)
    if event_type:
        q = q.filter(PeopleEvent.event_type == event_type)
    return q.order_by(PeopleEvent.ts.desc()).limit(min(limit, 5000)).all()


@router.get("/people-events/hourly")
async def get_hourly_traffic(
    start_date: str | None = None,
    end_date:   str | None = None,
    db: Session = Depends(get_db),
):
    """
    Aggregate 'in'/'out' counts by hour-of-day (0-23), summed across all days
    in range — answers "what hour do people mostly come and go".
    """
    q = db.query(
        func.extract("hour", PeopleEvent.ts).label("hour"),
        func.sum(case((PeopleEvent.event_type == "in", 1), else_=0)).label("in_count"),
        func.sum(case((PeopleEvent.event_type == "out", 1), else_=0)).label("out_count"),
    ).filter(PeopleEvent.event_type.in_(["in", "out"]))

    if start_date:
        q = q.filter(PeopleEvent.ts >= start_date)
    if end_date:
        q = q.filter(PeopleEvent.ts <= end_date)

    rows = q.group_by("hour").order_by("hour").all()
    by_hour = {int(r.hour): (int(r.in_count), int(r.out_count)) for r in rows}

    hours = list(range(24))
    return {
        "hours":      [f"{h:02d}:00" for h in hours],
        "in_counts":  [by_hour.get(h, (0, 0))[0] for h in hours],
        "out_counts": [by_hour.get(h, (0, 0))[1] for h in hours],
    }


@router.get("/store-status")
async def get_store_status(db: Session = Depends(get_db)):
    """
    Returns whether the store currently has detected activity (a person seen
    recently), and the timestamp of the last activity/in/out signal.
    """
    last = (
        db.query(PeopleEvent)
        .order_by(PeopleEvent.ts.desc())
        .first()
    )
    if not last:
        return {"active": False, "last_activity": None}

    active = (now_wib() - last.ts) <= timedelta(minutes=STORE_ACTIVE_WINDOW_MIN)
    return {"active": active, "last_activity": last.ts.isoformat()}
