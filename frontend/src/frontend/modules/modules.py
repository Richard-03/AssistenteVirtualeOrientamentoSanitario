from typing_extensions import Literal
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


class ClienteModel(BaseModel):
    nome:str=Field(..., max_length=20)
    cognome:str=Field(..., max_length=20)
    indirizzo:Optional[str]=Field(None, max_length=255)
    citta:Optional[str]=Field(None, max_length=100)
    email:EmailStr=Field(...)
    password:str=Field(..., max_length=255)
    eta:Optional[int]=Field(None, gt=0)
    sesso:Optional[Literal['M', 'F', 'Altro']]="Altro"
    peso:Optional[float]=Field(None, gt=0)
    altezza:Optional[float]=Field(None, gt=0)
    intolleranze:Optional[List[str]]=None
    condizioni_pregresse:Optional[List[str]]=None
    condizioni_familiari:Optional[List[str]]=None
    farmaci:Optional[List[str]]=None

class LoginModel(BaseModel):
    email: EmailStr
    password: str