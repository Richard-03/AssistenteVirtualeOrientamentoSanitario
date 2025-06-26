from fastapi import FastAPI, Query, Request, Form, HTTPException, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
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
from recensione.front_recensione import recensisci_form 


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
    request: Request,
    nome: str = Form(...),
    cognome: str = Form(...),
    codice_fiscale: str = Form(...),
    numero_albo: str = Form(...),
    citta_ordine: str = Form(...),
    data_iscrizione_albo: str = Form(...),
    citta: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    specializzazione: str = Form(...),
    tesserino: UploadFile = Form(...),
    telefono: str = Form(None),
    url_sito: str = Form(None),
    indirizzo: str = Form(None),
    stato: str = Form("Attivo"),
    disponibilita: str = Form(...)  # Nuovo campo obbligatorio
):
    try:
        result = await iscrizione_medico(
            request,
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
            stato,
            disponibilita  # Passaggio del campo
        )
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
    print("Ricevuto JSON in elimina_appuntamento_wrapper:", data)
    try:
        return elimina_appuntamento(request, data["id_appuntamento"])
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise



#metodi per la gestione della modifica del profilo
@app.get("/modifica_profilo")
def modifica_profilo_form_wrapper(request: Request):
    try:
        return modifica_profilo_form(request)
    except Exception as e:
        print("Catturata eccezione:", e, type(e))
        raise


@app.post("/modifica_profilo")
def modifica_profilo_wrapper(request: Request,
                             client_id: int = Form(...),
                             email: str = Form(...),
                             password: str = Form(None),
                             indirizzo: str = Form(None),
                             peso: float = Form(None),
                             farmaci: str = Form(None),
                             condizioni_pregresse: str = Form(None),
                             condizioni_familiari: str = Form(None)):
    try:
        def parse_list(s):
            return [item.strip() for item in s.split(',')] if s else []

        data = {
            "client_id": client_id,
            "email": email,
            "password": password,
            "indirizzo": indirizzo,
            "peso": peso,
            "farmaci": parse_list(farmaci),
            "condizioni_pregresse": parse_list(condizioni_pregresse),
            "condizioni_familiari": parse_list(condizioni_familiari),
            "intolleranze": [],  # Se non gestite nel form
        }

        response = requests.put(API_URL + "modifica_cliente", json=data)
        response.raise_for_status()
        return RedirectResponse("/dashboard_utente", status_code=302)

    except requests.RequestException as e:
        print("Catturata eccezione:", e)
        raise HTTPException(status_code=500, detail="Errore nella modifica del profilo")


@app.get("/medici_consigliati", response_class=JSONResponse)
def medici_consigliati_proxy(client_id: int, chat_number: int, latitude: Optional[float] = None, longitude: Optional[float] = None):
    try:
        response = requests.get(f"{API_URL}medici_consigliati", params={
            "client_id": client_id,
            "chat_number": chat_number,
            "latitude": latitude,
            "longitude": longitude
        })
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Errore nel proxy frontend:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero dei medici consigliati")



# endpoint per recensioni tramite mail differita

@app.get("/recensisci")
def inoltra_recensione_html(request: Request):
    try:
        return recensisci_form(request)
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        raise

@app.post("/recensisci")
def inoltra_recensione(
    id_appuntamento: int = Form(...),
    id_medico: int = Form(...),
    voto: int = Form(...),
    commento: str = Form(...)
):
    payload = {
        "id_appuntamento": id_appuntamento,
        "id_medico": id_medico,
        "voto": voto,
        "commento": commento
    }

    print("PARTE PAYLOAD: ", payload)

    try:
        r = requests.post(f"{API_URL}/recensisci", json=payload, timeout=5)
        r.raise_for_status()
        messaggio = "Grazie per la tua recensione!"
    except Exception:
        messaggio = "Errore durante l'invio della recensione."

    return HTMLResponse(f"""
        <html>
            <head>
                <script>
                    alert("{messaggio}");
                    window.location.href = "/";
                </script>
            </head>
            <body></body>
        </html>
    """)

@app.get("/giorni_disponibili")
def giorni_disponibili(id_medico: int):
    res = requests.get(API_URL + "giorni_disponibili", params={"id_medico": id_medico})
    return res.json()



@app.post("/verifica_slot")
async def verifica_slot_proxy(request: Request):
    data = await request.json()
    print("Ricevuti dati verifica_slot_proxy:", data)  # stampa dati ricevuti
    try:
        print("Dati inviati a backend get_slot_disponibili_medico:", data)  # stampa dati inviati
        response = requests.post(f"{API_URL}get_slot_disponibili_medico", json=data)
       
        response.raise_for_status()
        print("Risposta backend get_slot_disponibili_medico:", response.json())  # stampa risposta backend
        return JSONResponse(content=response.json())
    except requests.RequestException as e:
        print("Errore in verifica_slot_proxy:", e)
        raise HTTPException(status_code=500, detail="Errore nel verificare slot")

@app.post("/prenota_appuntamento")
async def prenota_appuntamento_proxy(request: Request):
    data = await request.json()
    print("Ricevuti dati prenota_appuntamento_proxy:", data)  # stampa dati ricevuti
    try:
        response = requests.post(f"{API_URL}prenota_appuntamento", json=data)
        print("Dati inviati a backend prenota_appuntamento:", data)  # stampa dati inviati
        response.raise_for_status()
        print("Risposta backend prenota_appuntamento:", response.json())  # stampa risposta backend
        return JSONResponse(content=response.json())
    except requests.RequestException as e:
        print("Errore in prenota_appuntamento_proxy:", e)
        raise HTTPException(status_code=500, detail="Errore nella prenotazione")

#endopint per aggiornare le disponbilita del medico 
@app.get("/aggiorna_disponibilita")
def form_aggiorna_disponibilita(request: Request):
    medico = request.session.get("medico")
    if not medico:
        raise HTTPException(status_code=401, detail="Utente non autenticato")
    return main_templates.TemplateResponse("aggiorna_disponibilita.html", {"request": request, "medico": medico})


@app.post("/aggiorna_disponibilita")
def invia_nuove_disponibilita(
    request: Request,
    disponibilita: str = Form(...)
):
    medico = request.session.get("medico")
    if not medico:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    try:
        response = requests.post(API_URL + "aggiorna_disponibilita", data={
            "id_medico": medico["id"],
            "disponibilita": disponibilita
        })
        response.raise_for_status()
        return RedirectResponse("/profilo_medico", status_code=303)
    except requests.RequestException as e:
        print("Errore durante aggiornamento disponibilità:", e)
        raise HTTPException(status_code=500, detail="Errore nel salvataggio delle nuove disponibilità")

# endpoint per eliminazioen della chat dell utente
@app.post("/elimina_chat")
def elimina_chat(request: Request, client_id: int = Form(...), chat_number: int = Form(...)):
    try:
        # Chiamata alla tua API backend per eliminare logicamente la chat
        response = requests.post("http://backend_name:8000/elimina_chat", data={
            "client_id": client_id,
            "chat_number": chat_number
        })
        response.raise_for_status()

        # Dopo l'eliminazione, reindirizza alla dashboard o alla pagina chat
        return RedirectResponse(f"/dashboard_utente?client_id={client_id}", status_code=302)
    except requests.RequestException as e:
        print("Errore durante l'eliminazione:", e)
        raise HTTPException(status_code=500, detail="Errore nell'eliminazione della conversazione")

# end point per il compplttaemnto dell apputamento 
@app.post("/completa_appuntamento")
def completa_appuntamento(
    request: Request,
    
    id_appuntamento: int = Form(...),
    diagnosi: str = Form(...)
):
    try:
        response = requests.post("http://backend_name:8000/completa_appuntamento", data={
            
            "id_appuntamento": id_appuntamento,
            "diagnosi": diagnosi
        })
        response.raise_for_status()
        return RedirectResponse("/agenda_medico", status_code=302)
    except requests.RequestException as e:
        print("Errore durante il completamento:", e)
        raise HTTPException(status_code=500, detail="Errore nel completare l'appuntamento")


@app.post("/elimina_appuntamento_utente")
def elimina_appuntamento_utente_wrapper(request: Request,id: int = Form(...)):
    try:
        print("ID ricevuto:", id)
        return elimina_appuntamento_utente(request, id)
    except Exception as e:
        print("Errore in elimina_appuntamento_utente_wrapper:", e)
        raise HTTPException(status_code=500, detail="Errore nell'eliminazione dell'appuntamento")


@app.get("/appuntamenti_utente")
def appuntamenti_utente_wrapper(request: Request):
    try:
        return visualizza_appuntamenti(request)
    except Exception as e:
        print("Errore in appuntamenti_utente_wrapper:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero degli appuntamenti")
