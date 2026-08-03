from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.events import router as event_router
from backend.routes.users import router as user_router
from backend.routes.stats import router as stats_router
from backend.routes.people import router as people_router
from backend.db import engine
from sqlalchemy import text
import json, logging, os
from logging.handlers import RotatingFileHandler

# ── Logging setup ──────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'backend.log'), maxBytes=5_000_000, backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s: %(message)s'
))
logging.getLogger('uvicorn').addHandler(file_handler)
logging.getLogger('uvicorn.access').addHandler(file_handler)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for c in dead:
            self.active_connections.remove(c)

app = FastAPI()
manager = ConnectionManager()

# Store manager in app state so routes can access it
app.state.manager = manager

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://iot.birmas.id",
        "http://170.64.149.147",
        "http://170.64.149.147:5173",
        "https://170.64.149.147",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(event_router, prefix="/api")
app.include_router(user_router, prefix="/api/users")
app.include_router(stats_router, prefix="/api")
app.include_router(people_router, prefix="/api")


@app.get("/api/health")
def health_check():
    """
    Lightweight liveness probe. Confirms the ASGI app is actually serving
    requests AND that the DB connection works — used by health_check.sh
    (cron, every 5 min) to detect a hung/zombie backend process, which
    `systemctl is-active` cannot see (a deadlocked process still shows as
    "active" to systemd even though it no longer answers any requests).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await app.state.manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.manager.disconnect(websocket)
