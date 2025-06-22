from fastapi import FastAPI, Query, Request, Form, HTTPException, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os, sys
import requests
from starlette.middleware.sessions import SessionMiddleware
from login_medici_front.frontend_login_iscrizione_medico import elimina_appuntamento
from login_admin_frontend.login_admin_frontend import (
    verifica_medico as verifica_medico_wrapper_backend,
    admin_login,
    admin_login_form,
    admin_dashboard,
)
from login_front.frontend_login_iscrizione_utente import *
from login_medici_front.frontend_login_iscrizione_medico import *
from login_medici_front.frontend_login_iscrizione_medico import agenda_medico as agenda_medico_func

app = FastAPI()

#directory dei templates
css_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates", "css")
template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")
main_templates = Jinja2Templates(directory=template_dir)

name1 = os.path.join(os.path.abspath(os.path.dirname(__file__)), "login_admin_frontend", "templates", "css")
name2 = os.path.join(os.path.abspath(os.path.dirname(__file__)), "login_medici_front", "templates", "css")
name3 = os.path.join(os.path.abspath(os.path.dirname(__file__)), "login_front", "templates", "css")

print(name3)

app.mount("/login_admin_frontend/css", StaticFiles(directory=name1), name="login_admin_frontend_css")
app.mount("/login_medici_front/css", StaticFiles(directory=name2), name="login_medici_front_css")
app.mount("/login_front/css", StaticFiles(directory=name3), name="login_front_css")
app.mount("/css", StaticFiles(directory=css_path), name="css")


app.add_middleware(SessionMiddleware, secret_key="una-chiave-molto-segreta")


#end poiint per la pagina principale
@app.get("/")
def index(request:Request):
    return main_templates.TemplateResponse("index.html", {"request": request})

#end point per il login dell'admin
@app.get("/admin/login")
def admin_login_form_wrapper(request: Request):
    try:
        return admin_login_form(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise


@app.post("/admin/login")
def admin_login_wrapper(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        return admin_login(request, email, password)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/admin/dashboard")
def admin_dashboard_wrapper(request: Request):
    try:
        return admin_dashboard(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/admin/verifica")
def verifica_medico_wrapper(request: Request, email: str = Form(...)):
    try:
        return verifica_medico_wrapper_backend(request, email)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise



#endpoint per l utente
@app.get("/iscrizione_utente")
def home_wrapper(request: Request):
    try:
        return home(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/iscrizione_utente")
def subscribe_wrapper(request: Request,
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
        return subscribe(request,
              nome,
              cognome,
              indirizzo,
              citta,
              email,
              password,
              eta,
              sesso,
              condzioni_pregresse,
              condizioni_familiari,
              farmaci,
              intolleranze,
              peso,
              altezza
        )
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

# NUOVO ENDPOINT
@app.get("/dashboard_utente")
def dashboard_wrapper(request: Request):
    try:
        return user_dashboard_page(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/login_utente")
def login_form_wrapper(request: Request):
    try:
        return login_form(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/login_utente")
def login_wrapper(  request: Request,
                    email:EmailStr=Form(...),
                    password:str=Form(...)):
    try:
        return login(request, email, password)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/chat")
def chat_page_wrapper(request: Request, client_id: int, chat_number: int):
    try:
        print(f"PROVANDO A FARE RESUME DI UNA CHAT PASSO # = {chat_number}")
        return chat_page(request, client_id, chat_number)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/chat/msg")
def chat_msg_wrapper(request: Request, data: dict = Body(...)):
    try:
        return chat_msg(request, data)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise 

# NUOVO ENDPOINT
@app.post("/chat/new")
def new_chat_front(request: Request, client_id: int = Form(...)):
    chat_number = requests.post(API_URL + "chat", json={"client_id": client_id}).json()
    return RedirectResponse(f"/chat?client_id={client_id}&chat_number={chat_number}", 302)

# NUOVO ENDOPOINT
@app.get("/chat/resume_all")
def resume_all_chat_wrapper(request: Request, client_id: int = Query(...)):
    try:
        return resume_all_chat(request, client_id)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise 


@app.get("/iscrizione_medico")
def home_iscrizione_medico_wrapper(request:Request):
    try:
        return home_iscrizione_medico(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/iscrizione_medico_submit")
async def iscrizione_medico_wrapper(
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
    try:
        result = await iscrizione_medico(  request,
                            nome,
                            cognome,
                            codice_fiscale,
                            numero_albo,
                            citta_ordine,
                            data_iscrizione_albo,
                            citta,
                            email,
                            password,
                            specializzazione,
                            tesserino,
                            telefono,
                            url_sito,
                            indirizzo,
                            stato)
        return result
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/login_medico")
def login_medico_form_wrapper(request:Request):
    try:
        return login_medico_form(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/login_medico")
def login_medico_wrapper(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    try:
        return login_medico(request, email, password)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/profilo_medico")
def profilo_medico_wrapper(request: Request):
    try:
        return profilo_medico(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/modifica_email")
def modifica_email_wrapper(request: Request, email: str = Form(...)):
    try:
        return modifica_email(request, email)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/logout")
def logout_wrapper(request: Request):
    try:
        return logout(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.get("/agenda_medico")
def agenda_medico(request: Request):
    try:
        return agenda_medico_func(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise






@app.post("/elimina_appuntamento")
def elimina_appuntamento_wrapper(request: Request, data: dict = Body(...)):
    print("✅ Ricevuto JSON in elimina_appuntamento_wrapper:", data)
    try:
        return elimina_appuntamento(request, data["id_appuntamento"])
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise
