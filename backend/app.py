from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.events import router as event_router
from backend.routes.users import router as user_router
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # If a client is dead, we'll clean them up later
                pass

app = FastAPI()
manager = ConnectionManager()

# Store manager in app state so routes can access it
app.state.manager = manager

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(event_router, prefix="/api")
app.include_router(user_router, prefix="/api/users")

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await app.state.manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.manager.disconnect(websocket)