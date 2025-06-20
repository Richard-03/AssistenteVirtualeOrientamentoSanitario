from fastapi import FastAPI,HTTPException
import mariadb
from typing import Optional, List
import bcrypt #libreria per la criptazione della password
from .modules import *
from .send_mail import *

# SE SI VUOLE MODIFICARE IL MODO DI CREARE CURSOR
# USO:
#   with get_cursor() as cursor:
#       cursor: mariadb.Cursor  # solo per avere gli hint di vscode
#       # qui le operazioni
#   # le operazioni di apertura, chiusura, fallimento sono già gestite


#connessione  a mariadb
from database.database import _get_connection
""" conn = mariadb.connect(
    host="127.0.0.1",
    port=3307,  # MODIFICATA
    user="root",    # MODIFICATA
    password="rootpassword",
    database="user_db"
) """

conn = _get_connection()

# funzione per creare correttamente la query SQL in caso di None e altri valori sensibili e apici singoli
def format_value(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    val = str(val).replace("'", "''")  
    return f"'{val}'"

# funzione di esecuzione della query per recupero di dati
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

# TODO: ci sarebbe da fare rollback se un iscrizione non va a buon fine, attualmente mi iscrivo, mi da internal server error e l'iscrizione è andata cmq a buon fine
# in questo modo se poi provo a iscrivermi di nuovo (perché penso non sia andata a buon fine) mi dice già registrato, errore di nuovo
def subscribe(cliente:ClienteModel):
    
    query_verify = f"SELECT email FROM Cliente WHERE email={format_value(cliente.email)}"#verifica se  gia l'utente esiste
    result=execute_query(conn,query_verify)

    if result!=[]:
        raise HTTPException(status_code=400, detail="ERROR:utente gia registrato")
    else:
        

        #Conversione delle liste in stringhe separate da virgole
        if cliente.intolleranze is not None:
            intolleranze_str=','.join(cliente.intolleranze)
        else:
            intolleranze_str=None

        if cliente.condizioni_pregresse is not None:
            condizioni_pregresse_str=','.join(cliente.condizioni_pregresse)
        else:
            condizioni_pregresse_str=None

        if cliente.condizioni_familiari is not None:
            condizioni_familiari_str=','.join(cliente.condizioni_familiari)
        else:
            condizioni_familiari_str=None

        if cliente.farmaci is not None:
            farmaci_str=','.join(cliente.farmaci)
        else:
            farmaci_str=None

        #criptazione della password
        password_criptata = bcrypt.hashpw(cliente.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        print("erorre prima blocco")

        #creazione della query che usero per la store procedure
        query_call = f"""CALL insert_cliente_completo(
            {format_value(cliente.nome)}, {format_value(cliente.cognome)}, {format_value(cliente.indirizzo)}, {format_value(cliente.citta)},
            {format_value(cliente.email)}, {format_value(password_criptata)}, {cliente.eta}, {format_value(cliente.sesso)},
            {format_value(cliente.peso)}, {format_value(cliente.altezza)},
            {format_value(intolleranze_str)}, {format_value(condizioni_pregresse_str)}, {format_value(condizioni_familiari_str)},
            {format_value(farmaci_str)}

        )"""

        print("errore dopo qui")

        try:
            execute_query(conn, query_call)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB ERROR: {str(e)}")

        # BLOCCO AGGIUNTO PER RECUPERARE L'ID DEL CLIENTE + ret
        row = execute_query(conn,
            # andrebbero usati i parametri non lo fstrings per motivi di sicurezza (SQL injection)
            f"SELECT id FROM Cliente WHERE email = '{cliente.email}'",          
        )
        if not row:
            raise HTTPException(status_code=500, detail="ID non trovato dopo l’inserimento")

        print("id = ", row)
        new_id = row[0][0]
        

        sendMail(cliente.email,cliente.nome,cliente.cognome)

        return new_id


def login(cliente:LoginModel):
    # MODIFICATA
    query = f"SELECT id, password FROM Cliente WHERE email={format_value(cliente.email)}"
    result = execute_query(conn, query)

    if not result:
        raise HTTPException(status_code=400, detail="Utente non registrato")

    # MODIFICATA
    client_id, password_criptata_db = result[0]
    if not bcrypt.checkpw(cliente.password.encode('utf-8'), password_criptata_db.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Password errata")

    # MODIFICATO
    return {"client_id": client_id}
    