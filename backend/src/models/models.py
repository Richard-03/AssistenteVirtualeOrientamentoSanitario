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

class RecensioneInput(BaseModel):
    id_appuntamento: int
    id_medico: int
    voto: int
    commento: str


class SlotRequest(BaseModel):
    id_medico: int
    giorno: str           
    orario_inizio: str    
    orario_fine: str      
    durata_minuti: int

class PrenotaRequest(BaseModel):
    id_cliente: int
    id_medico: int
    datetime_appuntamento: str 