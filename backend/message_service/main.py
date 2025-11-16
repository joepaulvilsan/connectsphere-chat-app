import os
import json
import pika  # Using the standard BLOCKING library
import threading  # To run the consumer in the background
import uuid
from fastapi import FastAPI, HTTPException
from cassandra.cluster import Cluster, Session
from cassandra.query import SimpleStatement
from schemas import MessageDisplay  # Import the display schema
from typing import List
from dotenv import load_dotenv

# Load .env variables (like CASSANDRA_HOST, RABBITMQ_HOST)
load_dotenv()

# --- App & Cassandra Connection Setup ---

app = FastAPI(
    title="ConnectSphere Message Service (Consumer)",
    description="Listens to RabbitMQ and saves messages to Cassandra."
)

cluster: Cluster | None = None
session: Session | None = None

# Get hosts from env vars, default to localhost/127.0.0.1 for local uvicorn
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

# --- RabbitMQ Consumer Callback ---
# This function is run by the 'pika' thread every time a message arrives

def on_message_received(ch, method, properties, body):
    """
    Callback function to process messages from RabbitMQ.
    """
    print(f"[Message Service] Received a new message from RabbitMQ!")
    
    if not session:
        print("[Message Service] Error: Cassandra session is not available. Message will be requeued.")
        # 'nack' tells RabbitMQ the message failed and should be re-queued
        ch.basic_nack(delivery_tag=method.delivery_tag)
        return

    try:
        # 1. Parse the message body (it's bytes, so decode it)
        data = json.loads(body.decode())
        
        # 2. Save the message to Cassandra
        cql_query = """
        INSERT INTO messages (conversation_id, message_id, sender_id, text)
        VALUES (%s, now(), %s, %s)
        """
        session.execute(cql_query, (
            data['conversation_id'],
            data['sender_id'],
            data['text']
        ))
        
        # 3. Acknowledge the message (tells RabbitMQ it's successfully processed)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[Message Service] Message for {data['conversation_id']} saved to Cassandra.")
        
    except Exception as e:
        print(f"[Message Service] Error processing message: {e}")
        # If saving fails, don't acknowledge, so RabbitMQ can retry
        ch.basic_nack(delivery_tag=method.delivery_tag)

# --- RabbitMQ Consumer Thread ---

def start_consumer():
    """
    Connects to RabbitMQ and starts consuming messages in a blocking loop.
    This function runs in its own thread.
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        
        # Declare the queue (ensures it exists)
        channel.queue_declare(queue='message_queue')
        
        # Set up the subscription to the queue
        channel.basic_consume(
            queue='message_queue',
            on_message_callback=on_message_received
        )
        
        print("[Message Service] RabbitMQ Consumer is waiting for messages...")
        channel.start_consuming()
        
    except pika.exceptions.AMQPConnectionError as e:
        print(f"[Message Service] Failed to connect to RabbitMQ: {e}. Retrying in 5s...")
        # In a real app, you'd have a robust retry loop here
    except Exception as e:
        print(f"[Message Service] Consumer error: {e}")

# --- FastAPI Lifecycle Events ---

@app.on_event("startup")
async def on_startup():
    """
    Connects to Cassandra and starts the RabbitMQ consumer in a 
    background thread.
    """
    global cluster, session
    
    # 1. Connect to Cassandra (same as before)
    try:
        cluster = Cluster([CASSANDRA_HOST], port=9042)
        session = cluster.connect()
        # Create keyspace and table if they don't exist
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS chat_app_keyspace
            WITH REPLICATION = { 
              'class' : 'SimpleStrategy', 
              'replication_factor' : 1 
            }
            """)
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
        print("[Message Service] Successfully connected to Cassandra!")
    except Exception as e:
        print(f"[Message Service] FATAL: Could not connect to Cassandra: {e}")
        return # Don't start consumer if DB is down

    # 2. Start the RabbitMQ consumer in a background thread
    # 'daemon=True' means the thread will close when the main app closes
    print("[Message Service] Starting RabbitMQ consumer thread...")
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

@app.on_event("shutdown")
async def on_shutdown():
    """Closes the Cassandra connection when the app stops."""
    if cluster:
        cluster.shutdown()
        print("[Message Service] Cassandra connection closed.")

# --- API Endpoints ---
#
# NOTICE: The @app.post("/send_message/") endpoint is GONE!
# This service no longer accepts messages via HTTP.
#

@app.get("/messages/{conversation_id}", response_model=List[MessageDisplay])
async def get_messages(conversation_id: str):
    """Endpoint to retrieve all messages for a specific conversation."""
    if not session:
        raise HTTPException(status_code=500, detail="Database not connected")
    try:
        cql_query = "SELECT * FROM messages WHERE conversation_id = %s"
        rows = session.execute(cql_query, (conversation_id,))
        
        # We can directly return the list of Row objects
        # FastAPI will use the 'MessageDisplay' response_model to serialize them
        return list(rows) 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")