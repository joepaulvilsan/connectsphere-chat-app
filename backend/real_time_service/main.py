from fastapi import FastAPI
from fastapi.websockets import WebSocket, WebSocketDisconnect
from connection_manager import ConnectionManager
app = FastAPI(
    title="ConnectSphere Real-Time Service",
    description="Manages WebSocket connections for real-time communication."
)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} disconnected")