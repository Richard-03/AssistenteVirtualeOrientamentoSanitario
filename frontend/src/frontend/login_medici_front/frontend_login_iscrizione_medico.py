from fastapi import FastAPI,Request,HTTPException,Form,UploadFile
from fastapi.templating import Jinja2Templates
from fastapi import Query
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from typing import List
import requests

import sys
import os
ROOT_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../'))
sys.path.append(ROOT_DIR)
from modules.modules import *

from fastapi.staticfiles import StaticFiles


#directory dei templates
TEMPLATE_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "templates"
)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# API_URL="http://localhost:8000/"
API_URL="http://backend_name:8000/"

#endpoint GET per caricamento di iscrizione.html
def home_iscrizione_medico(request:Request):
    return templates.TemplateResponse("iscrizione_medico.html", {"request": request, "valori_precedenti": {}})

async def iscrizione_medico(
    request:Request,
    nome:str=Form(...),
    cognome:str=Form(...),
    codice_fiscale:str=Form(...),
    numero_albo:str=Form(...),
    citta_ordine:str=Form(...),
    data_iscrizione_albo:str=Form(...),
    citta:str=Form(...),
    email:EmailStr=Form(...),
    password:str=Form(...),
    specializzazione: str = Form(...),
    tesserino:UploadFile=Form(...),
    telefono: str = Form(None),
    url_sito: str = Form(None),
    indirizzo: str = Form(None),
    stato: str = Form("Attivo")
):
    import tempfile
    import json

    form_data = await request.form()

    medico_data = {
        "nome": nome,
        "cognome": cognome,
        "codice_fiscale": codice_fiscale,
        "numero_albo": numero_albo,
        "citta_ordine": citta_ordine,
        "data_iscrizione_albo": data_iscrizione_albo,
        "citta": citta,
        "email": email,
        "password": password,
        "specializzazione": specializzazione,  # rimane stringa JSON
        "telefono": form_data.get("telefono"),
        "url_sito": form_data.get("url_sito"),
        "indirizzo": form_data.get("indirizzo"),
        "stato": form_data.get("stato", "Attivo")
    }

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(tesserino.file.read())
        tmp_path=tmp.name

    #invio form html con file allegati,multipart/form-data
    with open(tmp_path, "rb") as file:
        multipart_files = [
            ("tesserino", (tesserino.filename, file, "application/octet-stream")),
            ("nome", (None, nome)),
            ("cognome", (None, cognome)),
            ("codice_fiscale", (None, codice_fiscale)),
            ("numero_albo",(None, numero_albo)),
            ("citta_ordine", (None, citta_ordine)),
            ("data_iscrizione_albo", (None, data_iscrizione_albo)),
            ("citta", (None, citta)),
            ("email", (None, email)),
            ("password", (None, password)),
            ("telefono", (None, form_data.get("telefono"))),
            ("url_sito", (None, form_data.get("url_sito"))),
            ("indirizzo", (None, form_data.get("indirizzo"))),
            ("stato", (None, form_data.get("stato", "Attivo")))
        ]

        multipart_files.append(("specializzazione", (None, specializzazione)))

        response = requests.post(API_URL + "subscribe_medico", files=multipart_files)

    if response.status_code == 200:
        return RedirectResponse("/iscrizione_medico?successo=1", status_code=303)
    else:
        try:
            messaggio = response.json().get("detail", "Errore generico.")
        except Exception:
            messaggio = "Errore interno nel backend."
        return templates.TemplateResponse(
            "iscrizione_medico.html",
            {
                "request": request,
                "errore_backend": True,
                "messaggio_errore": messaggio,
                "valori_precedenti": medico_data
            }
        )






def login_medico_form(request:Request):
    return templates.TemplateResponse("login_medico.html",{"request":request})

def login_medico(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    try:
        response = requests.post(API_URL + "login_medico", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()

        medico_data = response.json()
        request.session["medico"] = medico_data
        return RedirectResponse("/profilo_medico", status_code=302)
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Errore nella comunicazione con il backend")

def profilo_medico(request: Request):
    medico = request.session.get("medico")
    return templates.TemplateResponse("profilo_medico.html", {"request": request, "medico": medico})

def modifica_email(request: Request, email: str = Form(...)):
    medico = request.session.get("medico")
    if not medico:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    try:
        response = requests.post(API_URL + "modifica_email", json={
            "id": medico["id"],
            "nuova_email": email
        })
        response.raise_for_status()

        medico["email"] = email
        request.session["medico"] = medico

        return RedirectResponse("/profilo_medico", status_code=302)
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Errore nella comunicazione col backend")


# Endpoint per gestire il logout
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login_medico", status_code=302)


# Endpoint per visualizzare l'agenda del medico autenticato
def agenda_medico(request: Request):
    medico = request.session.get("medico")
    if not medico:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    try:
        response = requests.get(API_URL + f"agenda_medico?id_medico={medico['id']}")
        response.raise_for_status()
        agenda = response.json()
        return templates.TemplateResponse("agenda_medico.html", {"request": request, "agenda": agenda, "medico": medico})
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Errore nella comunicazione col backend")


# Funzione per permettere al medico di eliminare un appuntamento


def elimina_appuntamento(request: Request, id_appuntamento: int):
    medico = request.session.get("medico")
    if not medico:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    try:
        response = requests.post(API_URL + "elimina_appuntamento", json={
            "id_appuntamento": id_appuntamento
        })
        response.raise_for_status()
        return RedirectResponse("/agenda_medico", status_code=302)
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Errore nella comunicazione col backend")