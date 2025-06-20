from pydantic import BaseModel
from typing import Optional, List

class LLM_Answer(BaseModel):
    sintomi: List[str]
    specialisti: List[str]
    potresti_avere: List[str] = None
    consigli_attuali: List[str] = None

class MessageRequest(BaseModel):
    client_id: int
    chat_id: int
    new_msg: str

class NewChatRequest(BaseModel):
    client_id: int
    chat_id: Optional[int] = None


class ChatRequest(NewChatRequest):
    chat_id: int    # enforces passing a non null argument