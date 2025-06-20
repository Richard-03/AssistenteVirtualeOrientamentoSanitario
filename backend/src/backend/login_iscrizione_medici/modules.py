from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import EmailStr
from datetime import date
from datetime import datetime

#tramite Field faccio una validazione dei dati ,gt ->valori strettamente >0, ... -> campo obbligaotorio


class MedicoModel(BaseModel):
    nome: str = Field(..., max_length=20)
    cognome: str = Field(..., max_length=20)
    codice_fiscale: str = Field(..., min_length=16, max_length=16)
    numero_albo: str = Field(..., max_length=20)
    citta_ordine: Optional[str] = Field(None, max_length=100)
    data_iscrizione_albo: date
    email: EmailStr = Field(...)
    password: str = Field(..., max_length=255)
    specializzazione: Optional[str] = None
    citta: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    url_sito: Optional[str] = Field(None, max_length=2083)
    indirizzo: Optional[str] = Field(None, max_length=255)
    stato: Optional[str] = Field(default="Attivo")
    

class MedicoLoginModel(BaseModel):
    email: EmailStr
    password: str


class AppuntamentoDeleteRequest(BaseModel):
    id_appuntamento: int
