from pydantion import BaseModel, Field
from typing import Optional

class MessageSchema(BaseModel):
    sender_id: str
    message_id: str
    conversation_id: str
    text: str