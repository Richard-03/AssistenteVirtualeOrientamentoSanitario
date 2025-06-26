import os
from database.chatting import fetch_db_pure_chat, fetch_all_chats_for_client, get_last_chat_number
from backend.llm_interaction.interaction import init_vma, llm_interact 
from models.models import NewChatRequest, MessageRequest, RecensioneInput
from backend.user.login import login, subscribe, get_cliente,elimina_appuntamento_logico, modifica_cliente,get_appuntamenti_cliente
from backend.user.modules import LoginModel, ClienteModel
from fastapi import FastAPI, HTTPException, status, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from typing import Any, List, Dict, Optional
from backend.admin.admin import login_admin, get_tesserino, get_utenti_non_verificati, verifica_medico
from backend.doctor.login_iscrizione import subscribe_medico, login_medico, modifica_email, get_agenda_medico 
from backend.doctor.modules import AppuntamentoDeleteRequest, MedicoLoginModel
from database.chatting import fetch_suggested_field as fetch_suggested_reparto, fetch_client_info
from backend.geo.geo import get_nearest_drs
from backend.ranking.review import scrivi_recensione
from config import SYSTEM_ROBUST_OUTPUT
from  models.models import PrenotaRequest,SlotRequest
from backend.doctor.agenda import aggiorna_disponibilita, elimina_appuntamento as elimina_appuntamento_logica
from database.chatting import get_giorni_disponibili_medico,get_slot_disponibili,prenota_appuntamento ,elimina_conversazione_logico,completa_appuntamento 

app = FastAPI()


#uso fastapi per la gestione delle immagini
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__),  "doctor", "uploads")), name="uploads")


#########################
#                       #
#   ENPOINT PER CHAT    #
#                       #
#########################


@app.post("/chat/msg")
def msg_to_llm(data: MessageRequest) -> str:
    print("ANCHE QUI CI ARRIVIAMO ")
    """Wrapper for LLM interaction"""
    try:
        llm_response = llm_interact(
            client_id=data.client_id,
            chat_number=data.chat_number,
            new_msg=data.new_msg,
            latitude=data.latitude,     # aggiunto per posizione dinamica, può essere None
            longitude=data.longitude    # //  
        )
        print("llm_response esiste = ", bool(llm_response))
        return llm_response
    except HTTPException as e:
        print("Catturata eccezione HTTP in endpoint: msg_to_llm: ", e, type(e))
        raise 
    except Exception as e:
        print("Catturata eccezione in endpoint: msg_to_llm: ", e, type(e))
        result = SYSTEM_ROBUST_OUTPUT
        return result

@app.post("/chat")
def new_chat(data: NewChatRequest) -> int:
    """Wrapper for initializzation of chat db structures"""
    try:
        last_chat_number = get_last_chat_number(data.client_id)
        # se l'ultima è #chat = N e voglio una nuova sarà #chat = N + 1
        next_chat_number = last_chat_number + 1
        init_vma(data.client_id, next_chat_number)
        return next_chat_number 
    except Exception as e:
        print("Catturata eccezione in endpoint: new_chat: ", e, type(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Creazione tabelle dei messaggi fallita nel database")

@app.get("/resume_all_chats")
def get_existing_chats(client_id: int) -> List[int]:
    """Wrapper for fatching all the chat of a user. Returns a list of ids"""
    try:
        return fetch_all_chats_for_client(client_id)  # ogni chat ha id, timestamp, ecc.
    except Exception as e:
        print("Catturata eccezione in endpoint: get_existing_chats: ", e, type(e))
        raise HTTPException(status_code=404, detail="Nessuna chat trovata")

@app.get("/resume_chat")
def get_existing_chat(client_id:int, chat_number:int) -> List[Dict[str, Any]]:
    """Wrapper for fetching chat in the db. Returns the history of a chat."""
    try:
        history = fetch_db_pure_chat(client_id, chat_number)
        return history
    except Exception as e:
        print("Catturata eccezione in endpoint: get_existing_chat: ", e, type(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "ERRORE: non esiste la tabella cercata, non dovresti poter fare questa chiamata, solo NEW")

@app.get("/medici_consigliati")
def get_medici_consigliati(client_id: int, chat_number: int, latitude: Optional[float] = None, longitude: Optional[float] = None):
    """Returns the list of doctors, in the form of dictionaries, which match the category extracted from the chat."""
    try:
        # Recupera il reparto suggerito
        reparto = fetch_suggested_reparto(client_id, chat_number)
        if not reparto:
            raise HTTPException(status_code=404, detail="Nessun reparto consigliato per questa chat.")

        # Recupera indirizzo del cliente
        client_info = fetch_client_info(client_id)
        indirizzo_cliente = client_info.get("indirizzo")
        if not indirizzo_cliente:
            raise HTTPException(status_code=400, detail="Indirizzo del cliente non disponibile.")

        # Calcola i medici ordinati per distanza
        medici_ordinati = get_nearest_drs(indirizzo_cliente, reparto, latitude, longitude)

        # Prepara i risultati
        medici = [{
            "id": m["id"],  # 👈 aggiungi questo campo!
            "nome": m["nome"],
            "cognome": m["cognome"],
            "specializzazione": m["specializzazione"],
            "indirizzo": m["indirizzo"],
            "distanza_km": round(m["distanza_km"], 2)
        } for m in medici_ordinati]


        return {"reparto": reparto, "medici": medici}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    
#endpoint per eliminazione della chat

@app.post("/elimina_chat")
def elimina_chat(client_id: int = Form(...), chat_number: int = Form(...)):
    try:
       
        return elimina_conversazione_logico(client_id, chat_number)
    except Exception as e:
        print("Errore in elimina_chat:", e)
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione della chat")

#########################
#                       #
#   ENPOINT PER CLIENTE #
#                       #
#########################

@app.post("/login_utente")  
def login_wrapper(cliente:LoginModel):
    """Endopoint-wrapper for user login"""
    try:
        return login(cliente)
    except Exception as e:
        print("Catturata eccezione in endpoint: login_wrapper: ", e, type(e))
        raise


@app.post("/subscribe")
def subscribe_wrapper(cliente:ClienteModel):   
    """Endopoint-wrapper for user subscription"""
    try:
        return subscribe(cliente)
    except Exception as e:
        print("Catturata eccezione in endpoint: subscribe_wrapper: ", e, type(e))
        raise

@app.get("/get_cliente")
def get_cliente_wrapper(id: int):
    try:
        return get_cliente(id)
    except Exception as e:
        print("Catturata eccezione in endpoint: get_cliente_wrapper: ", e, type(e))
        raise HTTPException(status_code=404, detail="Utente non trovato")

@app.put("/modifica_cliente")
def modifica_cliente_wrapper(data: dict):
    
    try:
        return modifica_cliente(data)
    except Exception as e:
        print("Catturata eccezione in endpoint: modifica_cliente_wrapper: ", e, type(e))
        raise HTTPException(status_code=500, detail="Errore nella modifica del profilo")

# endpoint per mail differita
@app.post("/recensisci")
def salva_recensione(recensione: RecensioneInput):
    try:
        # Salva recensione nel DB
        scrivi_recensione(
            id_appuntamento=recensione.id_appuntamento,
            id_medico=recensione.id_medico,
            voto=recensione.voto,
            commento=recensione.commento
        )
    except Exception as e:
        print("Catturata eccezione in endpoint: salva_recensione: ", e, type(e))
        raise

#endpoint per elimianre appuntamento 
@app.post("/elimina_appuntamento_utente")
def elimina_appuntamento(id: int = Form(...)):
    try:
        return elimina_appuntamento_logico(id)
    except Exception as e:
        print("Catturata eccezione in endpoint: elimina_appuntamento_utente_endpoint: ", e, type(e))
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'appuntamento da parte dell'utente")
    
#endpoint per recuperare gli appuntamenti del cliente 
@app.get("/appuntamenti_cliente")
def get_appuntamenti_cliente_endpoint(id_cliente: int):
    try:
        return get_appuntamenti_cliente(id_cliente)
    except Exception as e:
        print("Catturata eccezione in endpoint: get_appuntamenti_cliente_endpoint:", e)
        raise HTTPException(status_code=500, detail="Errore durante il recupero degli appuntamenti del cliente")


#########################
#                       #
#   ENPOINT PER MEDICO  #
#                       #
#########################


@app.post("/aggiorna_disponibilita")
def aggiorna_disponibilita_wrapper(
    id_medico: int = Form(...),
    disponibilita: str = Form(...)
):
    """Endopoint-wrapper per aggiornare le disponibilità del medico"""
    try:
        return aggiorna_disponibilita(id_medico=id_medico, disponibilita=disponibilita)
    except Exception as e:
        print("Errore in aggiorna_disponibilita_wrapper:", e)
        raise HTTPException(status_code=500, detail="Errore durante l'aggiornamento delle disponibilità")

@app.post("/subscribe_medico")
def subscribe_medico_wrapper(
    nome: str = Form(...),
    cognome: str = Form(...),
    codice_fiscale: str = Form(...),
    numero_albo: str = Form(...),
    citta_ordine: str = Form(...),
    data_iscrizione_albo: str = Form(...),
    citta: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    specializzazione: str = Form(...),
    tesserino: UploadFile = File(...),
    telefono: str = Form(None),
    url_sito: str = Form(None),
    indirizzo: str = Form(None),
    stato: str = Form(None),
    disponibilita: str = Form(...)  # AGGIUNTO QUI
):
    """Endopoint-wrapper for doctor subscription"""
    try:
        return subscribe_medico(
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
            disponibilita  # AGGIUNTO QUI
        )
    except Exception as e:
        print("Catturata eccezione in endpoint: subscribe_medico_wrapper: ", e, type(e))
        raise


@app.post("/login_medico")
def login_medico_wrapper(medico:MedicoLoginModel):
    """Endopoint-wrapper for doctor login"""
    try:
        return login_medico(medico)
    except Exception as e:
        print("Catturata eccezione in endpoint: login_medico_wrapper: ", e, type(e))
        raise

@app.post("/modifica_email")
def modifica_email_wrapper(data: dict):
    """Endopoint-wrapper to modify email"""
    try:
        return modifica_email(data)
    except Exception as e:
        print("Catturata eccezione in endpoint: modifica_email_wrapper: ", e, type(e))
        raise

@app.get("/agenda_medico")
def get_agenda_medico_wrapper(id_medico: int):
    """Endopoint-wrapper to get a doctor agenda"""
    try:
        return get_agenda_medico(id_medico)
    except Exception as e:
        print("Catturata eccezione in endpoint: get_agenda_medico_wrapper: ", e, type(e))
        raise
    
    

#########################
#                       #
#   ENPOINT PER ADMIN   #
#                       #
#########################

@app.post("/admin/login")
def login_admin_wrapper(email:str=Form(...),password:str=Form(...)):
    """Endopoint-wrapper for admin login"""
    try:
        return login_admin(email, password)
    except Exception as e:
        print("Catturata eccezione in endpoint: login_admin_wrapper: ", e, type(e))
        raise
    
@app.get("/admin/utenti_da_verificare")
def get_utenti_non_verificati_wrapper():
    """Endopoint-wrapper to get users not verified yet"""
    try:
        return get_utenti_non_verificati()
    except Exception as e:
        print("Catturata eccezione in endpoint: get_utenti_non_verificati: ", e, type(e))
        raise

@app.get("/admin/tesserino/{email}")
def get_tesserino_wrapper(email:str):
    """Endopoint-wrapper to get admin badge"""
    try:
        return get_tesserino(email)
    except Exception as e:
        print("Catturata eccezione in endpoint: get_tesserino_wrapper: ", e, type(e))
        raise

@app.post("/admin/verifica_medico")
def verifica_medico_wrapper(email:str=Form(...)):
    """Endopoint-wrapper to verify a doctor"""
    try:
        return verifica_medico(email)
    except Exception as e:
        print("Catturata eccezione in endpoint: verifica_medico_wrapper: ", e, type(e))
        raise

#################################
#                               #
#   ENPOINT PER APPUNTAMENTO    #
#                               #
#################################


@app.post("/elimina_appuntamento")
def elimina_appuntamento(data: AppuntamentoDeleteRequest):
    """Endopoint-wrapper to delete a visit"""
    id_appuntamento = data.id_appuntamento

    try:
        return elimina_appuntamento_logica(id_appuntamento)
    except Exception as e:
        print("Catturata eccezione in endpoint: elimina_appuntamento: ", e, type(e))
        raise HTTPException(status_code=500, detail=f"Errore durante l'eliminazione: {str(e)}")
    
@app.get("/giorni_disponibili")
def giorni_disponibili(id_medico: int):
    try:
        return get_giorni_disponibili_medico(id_medico)
    except Exception as e:
        print("Errore in giorni_disponibili:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero dei giorni disponibili")

@app.post("/get_slot_disponibili")
def api_get_slot_disponibili(slot_req: SlotRequest):
    try:
        print(f"Chiamata get_slot_disponibili con dati: {slot_req}")
        result = get_slot_disponibili(slot_req)
        print(f"Risultato get_slot_disponibili: {result}")
        return result
    except Exception as e:
        print("Errore in get_slot_disponibili:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero degli slot disponibili")

@app.post("/prenota_appuntamento")
def api_prenota_appuntamento(prenota_req: PrenotaRequest):
    try:
        print(f"Chiamata prenota_appuntamento con dati: {prenota_req}")
        result = prenota_appuntamento(prenota_req)
        print(f"Risultato prenota_appuntamento: {result}")
        return result
    except Exception as e:
        print("Errore in prenota_appuntamento:", e)
        raise HTTPException(status_code=500, detail="Errore durante la prenotazione")

@app.post("/completa_appuntamento")
def completa_appuntamento_endpoint(
    id_appuntamento: int = Form(...),
    diagnosi: str = Form(...)
):
    
    try:
        return completa_appuntamento(id_appuntamento, diagnosi)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))