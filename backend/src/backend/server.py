import os
from database.chatting import fetch_db_pure_chat, fetch_all_chats_for_client, get_last_chat_number
from backend.llm_interaction.interaction import init_vma, llm_interact 
from models.models import NewChatRequest, MessageRequest
from backend.login_back_utenti.login import login, subscribe
from backend.login_back_utenti.modules import LoginModel, ClienteModel
from fastapi import FastAPI, HTTPException, status, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from typing import Any, List, Dict
from backend.login_admin.admin import login_admin, get_tesserino, get_utenti_non_verificati, verifica_medico
from backend.login_iscrizione_medici.login_iscrizione import subscribe_medico, login_medico, modifica_email, get_agenda_medico, elimina_appuntamento as elimina_appuntamento_logica
from backend.login_iscrizione_medici.modules import AppuntamentoDeleteRequest, MedicoLoginModel


app = FastAPI()

#uso fastapi per la gestione delle immagini
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__),  "login_iscrizione_medici", "uploads")), name="uploads")




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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Errore durante la comunicazione con l'assistente medico AI")

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

@app.post("/subscribe_medico")
def subscribe_medico_wrapper(   nome: str = Form(...),
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
                                stato: str = Form(None)):
    """Endopoint-wrapper for doctor subscription"""
    try:
        return subscribe_medico(nome,
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


# TODO: cosa è questa?

@app.post("/modifica_email")
def modifica_email_wrapper(data: dict):
    """Endopoint-wrapper to modify email"""
    try:
        return modifica_email(data)
    except Exception as e:
        print("Catturata eccezione in endpoint: modifica_email_wrapper: ", e, type(e))
        raise
        
# TODO: cosa è questa?

@app.get("/agenda_medico")
def get_agenda_medico_wrapper(id_medico: int):
    """Endopoint-wrapper to get a doctor agenda"""
    try:
        return get_agenda_medico(id_medico)
    except Exception as e:
        print("Catturata eccezione in endpoint: get_agenda_medico_wrapper: ", e, type(e))
        raise
    


#Login per gli admin
@app.post("/admin/login")
def login_admin_wrapper(email:str=Form(...),password:str=Form(...)):
    """Endopoint-wrapper for admin login"""
    try:
        return login_admin(email, password)
    except Exception as e:
        print("Catturata eccezione in endpoint: login_admin_wrapper: ", e, type(e))
        raise
    





# TODO: cosa è questa

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

@app.post("/elimina_appuntamento")
def elimina_appuntamento(data: AppuntamentoDeleteRequest):
    """Endopoint-wrapper to delete a visit"""
    id_appuntamento = data.id_appuntamento

    try:
        return elimina_appuntamento_logica(id_appuntamento)
    except Exception as e:
        print("Catturata eccezione in endpoint: elimina_appuntamento: ", e, type(e))
        raise HTTPException(status_code=500, detail=f"Errore durante l'eliminazione: {str(e)}")