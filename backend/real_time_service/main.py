import os  # <-- FIX 1: Added the missing import
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager
from cassandra.cluster import Cluster, Session
from cassandra.query import SimpleStatement
import uuid

# Get Cassandra host from env var, default to 127.0.0.1 for local uvicorn
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")

app = FastAPI(
    title="ConnectSphere Real-Time Service",
    description="Manages WebSocket connections for real-time communication."
)

# Global variables to hold the connection
cluster: Cluster | None = None
session: Session | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize Cassandra connection on startup."""
    global cluster, session
    try:
        cluster = Cluster([CASSANDRA_HOST], port=9042)
        session = cluster.connect()
        print("Successfully connected to Cassandra!")
        
        # Create keyspace and table if they don't exist
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS chat_app_keyspace
            WITH REPLICATION = { 
              'class' : 'SimpleStrategy', 
              'replication_factor' : 1 
            }
            """)
        print("Keyspace 'chat_app_keyspace' is ready.")

        session.set_keyspace('chat_app_keyspace')

        session.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                conversation_id text,
                message_id timeuuid,
                sender_id int,
                text text,
                PRIMARY KEY ((conversation_id), message_id)
            ) WITH CLUSTERING ORDER BY (message_id ASC);
            """)
        print("Table 'messages' is ready.")
    except Exception as e:
        print(f"FATAL: Could not connect to Cassandra: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Cassandra connection on shutdown."""
    global cluster
    if cluster:
        cluster.shutdown()
    print("Cassandra connection closed.")

# Create a single instance of the manager
manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int): # Changed client_id to int for sender_id
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for JSON data from the client
            data = await websocket.receive_json()
            
            # --- FIX 2: Added logic to save the message to Cassandra ---
            if session:
                try:
                    cql_query = """
                    INSERT INTO messages (conversation_id, message_id, sender_id, text)
                    VALUES (%s, now(), %s, %s)
                    """
                    # We use the client_id from the URL as the sender_id
                    session.execute(cql_query, (
                        data['conversation_id'], 
                        client_id, 
                        data['text']
                    ))
                except Exception as e:
                    # Log the error but don't disconnect the user
                    print(f"Error saving message to Cassandra: {e}")
            # --- End of Fix 2 ---

            # Broadcast the message to all other users
            await manager.broadcast(f"Client #{client_id} says: {data['text']}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} disconnected")
    except Exception as e:
        # Handle other potential errors (like bad JSON)
        print(f"An error occurred with client #{client_id}: {str(e)}")
        manager.disconnect(websocket)