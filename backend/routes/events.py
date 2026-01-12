from fastapi import APIRouter
from ..schemas import Event
from ..db import get_connection

router = APIRouter()

@router.post("/events")
def post_event(ev: Event):
    conn = get_connection()
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO events(camera_id, ts, label, confidence, bbox) VALUES (%s, %s, %s, %s, %s)",
            (ev.camera_id, ev.ts, ev.label, ev.confidence, ev.bbox)
        )
    return {"ok": True}

@router.get("/events")
def get_events(camera_id: str):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT camera_id, ts, label, confidence, bbox FROM events WHERE camera_id=%s ORDER BY ts DESC LIMIT 100",
            (camera_id,)
        )
        rows = cur.fetchall()
    return [{"camera_id": r[0], "ts": r[1].isoformat(), "label": r[2], "confidence": r[3], "bbox": r[4]} for r in rows]
