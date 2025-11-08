from fastapi import FastAPI
from schemas import MessageSchema
from cassandra.cluster import Cluster, Session
from cassandra.query import SimpleStatement
import uuid
import os
from fastapi import HTTPException

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")

app = FastAPI(
    title="ConnectSphere Message Service",
    description="Handles messaging functionalities between users."
)   
# Connect to Cassandra
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

        # --- 3. Use the Keyspace ---
        # Tell the session to use this keyspace for all following commands
        session.set_keyspace('chat_app_keyspace')

        # --- 4. Create Table (if it doesn't exist) ---
        # This is your data model based on our discussion
        # We partition by conversation_id and sort by message_id
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
        # In a real app, you might want to exit if the DB connection fails

@app.on_event("shutdown")
async def shutdown_event():
    """Close Cassandra connection on shutdown."""
    global cluster, session
    if session:
        session.shutdown()
    if cluster:
        cluster.shutdown()
    print("Cassandra connection closed.")

@app.post("/send_message/")
async def send_message(message: MessageSchema):
    """Endpoint to send a message from one user to another."""
    if not session:
        return {"error": "Database connection not established."}
    try:
    # Insert message into Cassandra
        cql_query = SimpleStatement("""
            INSERT INTO messages (conversation_id, message_id, sender_id, text)
            VALUES (%s, now(), %s, %s)
        """)
        session.execute(cql_query, (message.conversation_id, message.sender_id, message.text))    
        return {"status": "Message sent", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")
    





@app.get("/messages/{conversation_id}")  # <-- Changed from /messages/
async def get_messages(conversation_id: str):
    """Endpoint to retrieve all messages for a specific conversation."""
    if not session:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # This is the query our data model was designed for!
        cql_query = "SELECT * FROM messages WHERE conversation_id = %s"
        
        # Pass the conversation_id as a tuple
        rows = session.execute(cql_query, (conversation_id,))
        
        # Convert the Cassandra Row objects into a list of dictionaries
        # so FastAPI can return them as JSON
        messages = [
            {
                "conversation_id": row.conversation_id,
                "message_id": row.message_id,
                "sender_id": row.sender_id,
                "text": row.text
            } for row in rows
        ]
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")