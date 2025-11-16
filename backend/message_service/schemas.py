from pydantic import BaseModel
import uuid

# This model defines the data we expect to receive
# from RabbitMQ and what we save to Cassandra.
class MessageSchema(BaseModel):
    conversation_id: str
    sender_id: int
    text: str

# This model can be used to define the API response
# for the GET endpoint, including the database-generated ID.
class MessageDisplay(BaseModel):
    conversation_id: str
    message_id: uuid.UUID
    sender_id: int
    text: str

    class Config:
        orm_mode = True