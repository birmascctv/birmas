import os
from fastapi import FastAPI
from fastapi import WebSocket
from pydantic import BaseModel
import psycopg2

DB_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DB_URL)
app = FastAPI()
clients = set()

class Event(BaseModel):
    camera_id: str
    ts: str
    label: str
    confidence: float
    bbox: list[float]

@app.post("/events")
def post_event(ev: Event):
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO events(camera_id, ts, label, confidence, bbox) VALUES (%s, %s, %s, %s, %s)",
            (ev.camera_id, ev.ts, ev.label, ev.confidence, ev.bbox)
        )
    for ws in list(clients):
        try: import json; ws.send_text(json.dumps(ev.dict()))
        except Exception: pass
    return {"ok": True}

@app.get("/events")
def get_events(camera_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT camera_id, ts, label, confidence, bbox FROM events WHERE camera_id=%s ORDER BY ts DESC LIMIT 100", (camera_id,))
        rows = cur.fetchall()
    return [{"camera_id": r[0], "ts": r[1].isoformat(), "label": r[2], "confidence": r[3], "bbox": r[4]} for r in rows]

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        clients.discard(ws)