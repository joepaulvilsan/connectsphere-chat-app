from pydantic import BaseModel

class MessageSchema(BaseModel):
    sender_id: str
    receiver_id: str
    conversation_id: str