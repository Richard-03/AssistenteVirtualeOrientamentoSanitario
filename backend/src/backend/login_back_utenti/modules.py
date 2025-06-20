from fastapi import FastAPI
from pydantic import BaseModel,Field
from typing import List,Optional 
from pydantic import EmailStr
from typing_extensions import Literal

#tramite Field faccio una validazione dei dati ,gt ->valori strettamente >0, ... -> campo obbligaotorio

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