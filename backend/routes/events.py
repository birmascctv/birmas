from fastapi import APIRouter, Request, HTTPException
from schemas import Event
from db import get_connection

router = APIRouter()

@router.post("/events")
async def post_event(ev: Event, request: Request):
    # 1. Save to Database
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO events(camera_id, ts, label, confidence, bbox) VALUES (%s, %s, %s, %s, %s)",
                (ev.camera_id, ev.ts, ev.label, ev.confidence, ev.bbox)
            )
        
        # 2. Broadcast to all WebSocket clients
        # We access the manager we stored in app.state
        manager = request.app.state.manager
        await manager.broadcast(ev.model_dump())
        
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/events")
async def get_events(camera_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT camera_id, ts, label, confidence, bbox FROM events WHERE camera_id=%s ORDER BY ts DESC LIMIT 100",
                (camera_id,)
            )
            rows = cur.fetchall()
        return [
            {"camera_id": r[0], "ts": r[1].isoformat(), "label": r[2], "confidence": r[3], "bbox": r[4]}
            for r in rows
        ]
    finally:
        conn.close()