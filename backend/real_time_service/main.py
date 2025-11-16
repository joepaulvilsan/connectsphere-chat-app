import os
import json
import aio_pika  # <-- Use the ASYNC library
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager
# (All cassandra imports are gone)

# --- App & RabbitMQ Connection ---
app = FastAPI()

# Get host from .env, default to 'localhost' for local uvicorn
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost") 

# These will hold the persistent connection and channel
rabbitmq_connection: aio_pika.RobustConnection | None = None
rabbitmq_channel: aio_pika.Channel | None = None


@app.on_event("startup")
async def on_startup():
    """Connects to RabbitMQ when the app starts."""
    global rabbitmq_connection, rabbitmq_channel
    try:
        # 1. How to connect? (Use aio_pika's async connect)
        rabbitmq_connection = await aio_pika.connect_robust(
            f"amqp://guest:guest@{RABBITMQ_HOST}/"
        )
        
        # 2. How to get a channel?
        rabbitmq_channel = await rabbitmq_connection.channel()
        
        # 3. How to ensure the queue exists?
        await rabbitmq_channel.declare_queue('message_queue')
        
        print("Real-Time Service: Connected to RabbitMQ!")
    except Exception as e:
        print(f"FATAL: Real-Time Service could not connect to RabbitMQ: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    """Closes the RabbitMQ connection."""
    if rabbitmq_channel:
        await rabbitmq_channel.close()
    if rabbitmq_connection:
        await rabbitmq_connection.close()
    print("Real-Time Service: RabbitMQ connection closed.")


manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json() # e.g., {"conversation_id": "...", "text": "..."}
            
            # --- THIS IS THE BLOCK THAT REPLACES session.execute() ---
            if rabbitmq_channel:
                try:
                    # 4. How to convert data? (Add client_id and convert to JSON string)
                    message_to_send = {
                        "conversation_id": data['conversation_id'],
                        "sender_id": client_id,
                        "text": data['text']
                    }
                    body = json.dumps(message_to_send).encode() # encode to bytes

                    # 5. How to publish?
                    await rabbitmq_channel.default_exchange.publish(
                        aio_pika.Message(body=body),
                        routing_key='message_queue' # 6. Routing key = queue name
                    )
                except Exception as e:
                    print(f"Error publishing message: {e}")
            # --- END OF BLOCK ---

            # Broadcast to other live clients
            await manager.broadcast(f"Client #{client_id} says: {data['text']}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} disconnected")
    except Exception as e:
        print(f"An error occurred with client #{client_id}: {str(e)}")
        manager.disconnect(websocket)