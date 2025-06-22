from pydantic import BaseModel
from typing import Optional

class MessageRequest(BaseModel):
    client_id: int
    chat_number: int
    new_msg: str
    # aggiunte per posizione dinamica
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class NewChatRequest(BaseModel):
    client_id: int
    chat_number: Optional[int] = None

class ChatRequest(NewChatRequest):
    chat_number: int    # enforces passing a non null argument