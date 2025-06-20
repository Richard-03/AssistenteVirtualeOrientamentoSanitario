from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import RedirectResponse
import mariadb
from typing import Optional, List
import bcrypt #libreria per la criptazione della password
from modules import *
from send_mail import *
import os


from database.database import _get_connection
#connessione  a mariadb


#funzione per creare correttamente la query SQL in caso di None e altri valori sensibili e apici singoli
def format_value(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    val = str(val).replace("'", "''")  
    return f"'{val}'"
#funzione di esecuzione della query per recupero di dati

def execute_query(connection: mariadb.Connection, query: str):
    cursor: mariadb.Cursor = connection.cursor()
    cursor.execute(query)

    results=[]

    #gestione dei risultati della store procedure
    while True:
        try:
            part = cursor.fetchall()
            results.extend(part)
        except mariadb.ProgrammingError:
            pass
        if not cursor.nextset(): #passaggio al prossimo blocco di risultati
            break

    connection.commit()
    cursor.close()
    return results
#funzione per inserimento dati
def insert_data_query(connection:mariadb.Connection,query:str):
    try: 
        cursor:mariadb.Cursor=connection.cursor()
        cursor.execute(query)
        connection.commit()
        cursor.close()
        return True
    except mariadb.Error as e:
        
        print("ERROR:errore nell inserimento nel db")
        return False 
    


#ho dovuto usare i cmapi form perche mi dava problemi il carivcamento di file


def subscribe_medico(
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
    stato: str = Form(None)
):
    import json
    import requests

    print("DEBUG: ricevuti i dati:")
    print(f"{nome=}, {cognome=}, {codice_fiscale=}, {numero_albo=}, {citta_ordine=}")
    print(f"{data_iscrizione_albo=}, {citta=}, {email=}, {password=}, {specializzazione=}")
    print(f"{telefono=}, {url_sito=}, {indirizzo=}, {stato=}, {tesserino.filename=}")
    medico=MedicoModel(
        nome=nome,
        cognome=cognome,
        codice_fiscale=codice_fiscale,
        numero_albo=numero_albo,
        citta_ordine=citta_ordine,
        data_iscrizione_albo=data_iscrizione_albo,
        citta=citta,
        email=email,
        password=password,
        specializzazione=specializzazione,
        telefono=telefono,
        url_sito=url_sito,
        indirizzo=indirizzo,
        stato=stato
    )
    query_verify = f"SELECT email FROM Medico WHERE email={format_value(medico.email)}"#verifica se  il medico gia e registrato
    conn = _get_connection()
    result=execute_query(conn,query_verify)
    if result!=[]:
        raise HTTPException(status_code=400, detail="Email già registrata. Hai già un account?")
    else:

        try:
            specializzazione_list = json.loads(medico.specializzazione)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Il formato della specializzazione non è valido. Inviare una lista JSON di oggetti.")

        def get_lat_lon_from_address(address):
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": address, "format": "json"}
            headers = {"User-Agent": "FastAPI-app"}
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                if not data:
                    return None, None
                return data[0]["lat"], data[0]["lon"]
            except Exception as e:
                print(f"Errore nel calcolo lat/lon: {e}")
                return None, None

        latitudine, longitudine = get_lat_lon_from_address(medico.indirizzo)

        #criptazione password
        password_criptata = bcrypt.hashpw(medico.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        query_call=f"""CALL insert_medico_completo(
            {format_value(medico.nome)},
            {format_value(medico.cognome)},
            {format_value(medico.codice_fiscale)},
            {format_value(medico.numero_albo)},
            {format_value(medico.citta_ordine)},
            {format_value(medico.data_iscrizione_albo)},
            {format_value(medico.citta)},
            {format_value(medico.email)},
            {format_value(password_criptata)},
            {format_value(medico.telefono)},
            {format_value(medico.url_sito)},
            {format_value(medico.indirizzo)}
        )"""

        # Salva il file tesserino 
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        tesserino_path = os.path.join(upload_dir, f"{medico.email}_tesserino_{tesserino.filename}")
        with open(tesserino_path, "wb") as f:
            f.write(tesserino.file.read())

        try:
            execute_query(conn, query_call)
            id_query = f"SELECT id FROM Medico WHERE email={format_value(medico.email)}"
            id_result = execute_query(conn, id_query)
            if not id_result:
                raise HTTPException(status_code=500, detail="Registrazione incompleta: impossibile recuperare l'ID del medico.")

            id_medico = id_result[0][0]

            for item in specializzazione_list:
                spec = item.get("specializzazione")

                if not spec:
                    continue

                insert_spec = f"""
                INSERT INTO Specializzazione (id_medico, specializzazione, indirizzo, latitudine, longitudine, stato, ranking)
                VALUES (
                    {format_value(id_medico)},
                    {format_value(spec)},
                    {format_value(medico.indirizzo)},
                    {format_value(latitudine)},
                    {format_value(longitudine)},
                    'Attivo',
                    1
                )
                """
                insert_data_query(conn, insert_spec)
        except Exception as e:
            print(f"ERRORE DB: {e}")
            raise HTTPException(status_code=500, detail="Errore nel salvataggio dei dati. Riprova più tardi o contatta l'assistenza.")

        sendMail(medico.email, medico.nome, medico.cognome)
        return {"message": "Registrazione completata con successo"}
    



def login_medico(medico:MedicoLoginModel):
    conn = _get_connection()
    query=f"SELECT password, verificato FROM Medico WHERE email={format_value(medico.email)}"
    result=execute_query(conn, query)

    if not result:
        raise HTTPException(status_code=400, detail="Utente non registrato")

    password_criptata_db, verificato = result[0]
    if not verificato:
        raise HTTPException(status_code=403, detail="Utente da verificare. Attendere la conferma dell'amministratore.")

    if not bcrypt.checkpw(medico.password.encode('utf-8'), password_criptata_db.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Password errata")

    # Recupera anche gli altri dati del medico
    query_dati = f"""
    SELECT M.id, M.nome, M.cognome, M.email, M.telefono, M.url_sito, M.indirizzo,
           M.codice_fiscale, M.numero_albo, M.citta_ordine, M.data_iscrizione_albo, M.citta,
           GROUP_CONCAT(S.specializzazione SEPARATOR ',') AS specializzazioni
    FROM Medico M
    LEFT JOIN Specializzazione S ON M.id = S.id_medico
    WHERE M.email={format_value(medico.email)}
    GROUP BY M.id, M.nome, M.cognome, M.email, M.telefono, M.url_sito, M.indirizzo,
             M.codice_fiscale, M.numero_albo, M.citta_ordine, M.data_iscrizione_albo, M.citta
    """
    dati = execute_query(conn, query_dati)

    if not dati:
        raise HTTPException(status_code=500, detail="Errore nel recupero dati del medico")

    id_medico, nome, cognome, email, telefono, url_sito, indirizzo, codice_fiscale, numero_albo, citta_ordine, data_iscrizione_albo, citta, specializzazioni_str = dati[0]
    specializzazioni = specializzazioni_str.split(",") if specializzazioni_str else []

    return {
        "id": id_medico,
        "nome": nome,
        "cognome": cognome,
        "email": email,
        "telefono": telefono,
        "url_sito": url_sito,
        "indirizzo": indirizzo,
        "codice_fiscale": codice_fiscale,
        "numero_albo": numero_albo,
        "citta_ordine": citta_ordine,
        "data_iscrizione_albo": data_iscrizione_albo,
        "citta": citta,
        "specializzazione": specializzazioni
    }


# Endpoint per modificare l'email del medico

def modifica_email(data: dict):
    conn = _get_connection()
    id_medico = data.get("id")
    nuova_email = data.get("nuova_email")

    if not id_medico or not nuova_email:
        raise HTTPException(status_code=400, detail="Dati mancanti")

    query = f"UPDATE Medico SET email={format_value(nuova_email)} WHERE id={format_value(id_medico)}"
    
    try:
        execute_query(conn, query)
        return {"message": "Email aggiornata con successo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'aggiornamento: {str(e)}")


# Endpoint per ottenere l'agenda del medico autenticato

def get_agenda_medico(id_medico: int):
    conn = _get_connection()
    query = f"""
    SELECT 
        a.id AS id_appuntamento,
        a.appuntamento,
        a.stato AS stato_appuntamento,
        c.nome AS nome_cliente,
        c.cognome AS cognome_cliente
    FROM Agenda a
    JOIN Cliente c ON c.id = a.id_cliente
    WHERE a.id_medico = {format_value(id_medico)}
      AND a.stato != 'Eliminato'
    ORDER BY a.appuntamento ASC;
    """
    try:
        result = execute_query(conn, query)
        return result
    except Exception as e:
        print(f"ERRORE AGENDA MEDICO: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nel recupero dell'agenda: {str(e)}")


# Endpoint per eliminare un appuntamento (aggiorna lo stato a 'Eliminato')
def elimina_appuntamento(id_appuntamento: int):
    conn = _get_connection()
    query = f"""
    UPDATE Agenda
    SET stato = 'Eliminato'
    WHERE id = {id_appuntamento} 
    """

    try:
        execute_query(conn, query)
        return {"message": "Appuntamento eliminato con successo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'eliminazione: {str(e)}")
