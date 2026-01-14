import os
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import events   # import your events router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the events router
app.include_router(events.router)

clients = set()

# Optional: WebSocket endpoint
@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        clients.discard(ws)
