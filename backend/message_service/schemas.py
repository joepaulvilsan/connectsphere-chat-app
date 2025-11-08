from pydantic import BaseModel

class MessageSchema(BaseModel):
    sender_id: str
    message_id: str
    conversation_id: str
    text: str