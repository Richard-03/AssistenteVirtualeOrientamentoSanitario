from fastapi import Body, Query
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates

from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import EmailStr
from typing import List
import requests

import sys
import os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
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
def home(request: Request):
    return templates.TemplateResponse("iscrizione_utente.html",{"request": request})


def subscribe(request: Request,
              nome:str=Form(...),
              cognome:str=Form(...),
              indirizzo:str=Form(None),
              citta:str=Form(None),
              email:EmailStr=Form(...),
              password:str=Form(...),
              eta:int=Form(None),
              sesso:str=Form("Altro"),
              condzioni_pregresse:str=Form(None),
              condizioni_familiari:str=Form(None),
              farmaci:str=Form(None),
              intolleranze:str=Form(None),
              peso:float=Form(None),
              altezza:float=Form(None)
):
    try:
        def parse_list(s):
            return [item.strip() for item in s.split(',')] if s else None

        cliente=ClienteModel(
            nome=nome,
            cognome=cognome,
            indirizzo=indirizzo,
            citta=citta,
            email=email,
            password=password,
            eta=eta,
            sesso=sesso,
            peso=peso,
            altezza=altezza,
            intolleranze=parse_list(intolleranze),
            condizioni_pregresse=parse_list(condzioni_pregresse),
            condizioni_familiari=parse_list(condizioni_familiari),
            farmaci=parse_list(farmaci)
        )

        # MODIFICATO FINO A ret

        response=requests.post(API_URL+"subscribe", json=cliente.dict())
        response.raise_for_status()
        client_id = response.json() #["cliente"]
        print("Recuperato id utente iscritto dal db: ", client_id)
        
        # salva l'id nella sessione
        request.session["client_id"] = client_id

        return RedirectResponse("/dashboard_utente", status_code=302)
        

    except Exception as e:
        print("Eccezione nell'iscrizione: ", e, type(e))
        raise HTTPException(status_code=400, detail="Errore nell'iscrizione")
    

# NUOVA FUNZIONE
def user_dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "client_id": request.session["client_id"],
    })


def login_form(request: Request, error: str = None):
    return templates.TemplateResponse("login_utente.html", {"request": request, "error": error})

def login(request: Request,
          email:EmailStr=Form(...),
          password:str=Form(...)):
    cliente=LoginModel(email=email,password=password)
    try:
        # MODIFICATO
        response = requests.post(API_URL + "login_utente", json=cliente.dict())
        response.raise_for_status()
        client_id = response.json()["client_id"]
        request.session["client_id"] = client_id
        # MODIFICATO REINDIRIZZAMENTO
        return RedirectResponse("/dashboard_utente", status_code=302)
    except requests.RequestException as e:
        return login_form(request, error="Email o password errati.")

# SOSTITUZIONE
# Endpoint GET per visualizzare la pagina della chat utente
""" def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
 """

def chat_page(request: Request, client_id: int, chat_id: int):
    res = requests.get(API_URL + "resume_chat", params={"client_id": client_id, "chat_id": chat_id})
    if res.status_code == 404:
        return HTMLResponse("Chat non trovata", status_code=404)

    history = res.json()
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "client_id": client_id,
        "chat_id": chat_id,
        "history": history
    })



# Endpoint POST per inviare un messaggio alla chat (inoltra la richiesta al backend)
def chat_msg(request: Request, data: dict = Body(...)):
    response = requests.post(API_URL + "chat/msg", json=data)
    return response.text


# NUOVA
def resume_all_chat(request: Request, client_id: int = Query(...)):
    res = requests.get(API_URL + "resume_all_chats", params={"client_id": client_id})
    if res.status_code == 404:
        return RedirectResponse(f"/chat/new?client_id={client_id}", 302)

    chat_list = res.json()  # lista di chat_id + metadata
    print("Lista di id trovata: ", chat_list)
    return templates.TemplateResponse("chat_list.html", {
        "request": request,
        "client_id": client_id,
        "chat_list": chat_list
    })
