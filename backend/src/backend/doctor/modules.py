from pydantic import BaseModel, Field, EmailStr, root_validator
from typing import List, Optional
from datetime import date, datetime

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
    disponibilita: List[str] = Field(..., min_items=1)

    @root_validator(skip_on_failure=True)
    def check_datetime_format(cls, values):
        disponibilita = values.get("disponibilita")
        formato = "%Y-%m-%d %H:%M:%S"
        for dt_str in disponibilita:
            try:
                datetime.strptime(dt_str, formato)
            except ValueError:
                raise ValueError(f"Data/ora '{dt_str}' non valida. Usa il formato '{formato}'")
        return values

class MedicoLoginModel(BaseModel):
    email: EmailStr
    password: str


class AppuntamentoDeleteRequest(BaseModel):
    id_appuntamento: int
