from fastapi import FastAPI
from schemas import MessageSchema


app = FastAPI(
    title="ConnectSphere Message Service",
    description="Handles messaging functionalities between users."
)   

fake_db = []

@app.post("/send_message/")
async def send_message(message: MessageSchema):
    """Endpoint to send a message from one user to another."""
    fake_db.append(message)
    return {"status": "Message sent", "message": message}

@app.get("/messages/")
async def get_messages():
    """Endpoint to retrieve all messages."""
    return fake_db