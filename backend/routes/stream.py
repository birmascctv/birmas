from fastapi import WebSocket, APIRouter

router = APIRouter()
clients = set()

@router.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        clients.discard(ws)

def broadcast_event(event_dict):
    import json
    for ws in list(clients):
        try:
            ws.send_text(json.dumps(event_dict))
        except:
            clients.discard(ws)
