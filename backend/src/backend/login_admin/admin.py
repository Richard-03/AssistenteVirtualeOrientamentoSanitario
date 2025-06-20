from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import sys
import bcrypt

# Path per importare login_iscrizione
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "login_iscrizione_medici")))
from ..login_iscrizione_medici.login_iscrizione import execute_query, insert_data_query, format_value

from database.database import _get_connection
conn = _get_connection()


def login_admin(email:str=Form(...),password:str=Form(...)):
    query = f"SELECT password FROM Admin WHERE email = {format_value(email)}"
    try:
        result = execute_query(conn, query)
        if not result:
            raise HTTPException(status_code=404, detail="Admin non trovato")

        hashed_password = result[0][0]
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Password errata")

        return {"message": "Login effettuato con successo", "email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel login admin: {str(e)}")

#get per richiamare un query che recupera tutti i medici non verificati

def get_utenti_non_verificati():
    query = "SELECT nome, cognome, email FROM Medico WHERE verificato=0"
    try:
        result = execute_query(conn, query)
        utenti = [{"nome": r[0], "cognome": r[1], "email": r[2]} for r in result]
        return {"da_verificare": utenti}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero utenti: {str(e)}")

#get che prende in input un mail per cercare il tesserino associato alla mail

def get_tesserino(email:str):
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../uploads"))
    for filename in os.listdir(upload_dir):
        if filename.startswith(email) and "tesserino" in filename:
            return RedirectResponse(url=f"/uploads/{filename}")
    raise HTTPException(status_code=404, detail="Tesserino non trovato")

#get per aggiornare lo stato di un medico

def verifica_medico(email:str=Form(...)):
    query = f"UPDATE Medico SET verificato=1 WHERE email={format_value(email)}"
    try:
        success = insert_data_query(conn, query)
        if success:
            return {"message": f"Medico con email {email} verificato con successo"}
        else:
            raise HTTPException(status_code=500, detail="Errore durante la verifica")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore verifica: {str(e)}")