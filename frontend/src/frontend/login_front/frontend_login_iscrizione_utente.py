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
              nome: str = Form(...),
              cognome: str = Form(...),
              indirizzo: str = Form(None),
              citta: str = Form(None),
              email: EmailStr = Form(...),
              password: str = Form(...),
              eta: int = Form(None),
              sesso: str = Form("Altro"),
              condzioni_pregresse: str = Form(None),
              condizioni_familiari: str = Form(None),
              farmaci: str = Form(None),
              intolleranze: str = Form(None),
              peso: float = Form(None),
              altezza: float = Form(None)
):
    def parse_list(s):
        return [item.strip() for item in s.split(',')] if s else None

    cliente = ClienteModel(
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

    try:
        response = requests.post(API_URL + "subscribe", json=cliente.dict())
        response.raise_for_status()
        client_id = response.json()
        print("Recuperato id utente iscritto dal db: ", client_id)

        request.session["client_id"] = client_id
        return RedirectResponse("/dashboard_utente", status_code=302)

    except requests.HTTPError as e:
        if e.response.status_code == 400:
            error_detail = e.response.json().get("detail", "Errore nell'iscrizione")
            return templates.TemplateResponse("iscrizione_utente.html", {
                "request": request,
                "error": error_detail
            })
        else:
            print("Errore HTTP non previsto:", e)
            raise HTTPException(status_code=500, detail="Errore imprevisto nell'iscrizione")
    except Exception as e:
        print("Eccezione generica nell'iscrizione:", e)
        raise HTTPException(status_code=500, detail="Errore generico nell'iscrizione")


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

def chat_page(request: Request, client_id: int, chat_number: int):
    print(f"CHIAMATA A RESUME_CHAT CON NUMERO CHAT= {chat_number}")
    res = requests.get(API_URL + "resume_chat", params={"client_id": client_id, "chat_number": chat_number})
    if res.status_code == 404:
        return HTMLResponse("Chat non trovata", status_code=404)

    history = res.json()

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "client_id": client_id,
        "chat_number": chat_number,
        "history": history
    })



# Endpoint POST per inviare un messaggio alla chat (inoltra la richiesta al backend)
def chat_msg(request: Request, data: dict = Body(...)):
    print(f"QUI CI ARRIVIAMO con data {data}")
    response = requests.post(API_URL + "chat/msg", json=data)
    return response.text


# NUOVA
def resume_all_chat(request: Request, client_id: int = Query(...)):
    res = requests.get(API_URL + "resume_all_chats", params={"client_id": client_id})
    if res.status_code == 404:
        return RedirectResponse(f"/chat/new?client_id={client_id}", 302)

    chat_list = res.json()  # lista di chat_number + metadata
    print("Lista di id trovata: ", chat_list)
    return templates.TemplateResponse("chat_list.html", {
        "request": request,
        "client_id": client_id,
        "chat_list": chat_list
    })


#funzione per restituire i dati ionseriti dall utente
def modifica_profilo_form(request: Request):
    client_id = request.session.get("client_id")
    if not client_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    res = requests.get(API_URL + f"get_cliente?id={client_id}")
    if res.status_code != 200:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    cliente = res.json()
    return templates.TemplateResponse("modifica_profilo.html", {
        "request": request,
        "client_id": client_id,
        "email": cliente["email"],
        "password": cliente["password"],
        "indirizzo": cliente.get("indirizzo", ""),
        "peso": cliente.get("peso", ""),
        "farmaci": ", ".join(cliente.get("farmaci", [])) if cliente.get("farmaci") else "",
        "condizioni_pregresse": ", ".join(cliente.get("condizioni_pregresse", [])) if cliente.get("condizioni_pregresse") else "",
        "condizioni_familiari": ", ".join(cliente.get("condizioni_familiari", [])) if cliente.get("condizioni_familiari") else ""
    })

def modifica_profilo(
    request: Request,
    client_id: int,
    email: EmailStr,
    password: str,
    indirizzo: str,
    peso: float,
    farmaci: str,
    condizioni_pregresse: str,
    condizioni_familiari: str
):
    def parse_list(s):
        return [item.strip() for item in s.split(',')] if s else []

    data = {
        "id": client_id,
        "email": email,
        "password": password,
        "indirizzo": indirizzo,
        "peso": peso,
        "farmaci": parse_list(farmaci),
        "condizioni_pregresse": parse_list(condizioni_pregresse),
        "condizioni_familiari": parse_list(condizioni_familiari),
    }

    try:
        response = requests.put(API_URL + "modifica_cliente", json=data)
        response.raise_for_status()
        return RedirectResponse("/dashboard_utente", status_code=302)
    except requests.RequestException as e:
        print("Errore nella richiesta al backend:", e)
        raise HTTPException(status_code=500, detail="Errore nella modifica del profilo")


#funzione per cancellazione appuntamento 
def elimina_appuntamento_utente(request: Request,id:int=Form(...)):
    try:
        response = requests.post(API_URL + "elimina_appuntamento_utente", data={"id": id})

        response.raise_for_status()
        return RedirectResponse("/dashboard_utente", status_code=302)
    except requests.RequestException as e:
        print("Errore nell'eliminazione:", e)
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'appuntamento")
    
#funzione per recuperare appuntamenti del cliente 
def visualizza_appuntamenti(request: Request):
    client_id = request.session.get("client_id")
    if not client_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    try:
        response = requests.get(API_URL + f"appuntamenti_cliente?id_cliente={client_id}")
        response.raise_for_status()
        appuntamenti = response.json()
        print("Appuntamenti ricevuti dal backend:", appuntamenti)
        return templates.TemplateResponse("lista_appuntamenti.html", {
            "request": request,
            "client_id": client_id,
            "appuntamenti": appuntamenti
        })

      
    except requests.RequestException as e:
        print("Errore nel recupero degli appuntamenti:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero degli appuntamenti")
