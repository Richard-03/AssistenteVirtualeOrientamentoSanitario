from fastapi import HTTPException
import mariadb
import bcrypt #libreria per la criptazione della password
from .modules import *
from backend.email.send_email import send_mail_for_user_subscription, send_appointment_cancellation

from database.database import _get_connection



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
    conn = _get_connection()
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
    conn = _get_connection()
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
    conn = _get_connection()
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

        #creazione della query che usero per la store procedure
        query_call = f"""CALL insert_cliente_completo(
            {format_value(cliente.nome)}, {format_value(cliente.cognome)}, {format_value(cliente.indirizzo)}, {format_value(cliente.citta)},
            {format_value(cliente.email)}, {format_value(password_criptata)}, {cliente.eta}, {format_value(cliente.sesso)},
            {format_value(cliente.peso)}, {format_value(cliente.altezza)},
            {format_value(intolleranze_str)}, {format_value(condizioni_pregresse_str)}, {format_value(condizioni_familiari_str)},
            {format_value(farmaci_str)}

        )"""

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
        

        send_mail_for_user_subscription(cliente.email,cliente.nome,cliente.cognome)

        return new_id


def login(cliente:LoginModel):
    conn = _get_connection()
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
    



def get_cliente(id: int):
    conn = _get_connection()
    
    # Recupero dati base del cliente
    query_cliente = f"""
    SELECT id, nome, cognome, indirizzo, citta, email, password, eta, sesso, peso, altezza
    FROM Cliente WHERE id = {id}
    """
    result = execute_query(conn, query_cliente)

    if not result:
        raise HTTPException(status_code=404, detail="Cliente non trovato")

    row = result[0]
    keys = ["id", "nome", "cognome", "indirizzo", "citta", "email", "password", "eta", "sesso", "peso", "altezza"]
    cliente_dict = dict(zip(keys, row))


    def fetch_lista(tabella, campo):
        query = f"SELECT {campo} FROM {tabella} WHERE id_cliente = {id} AND stato = 'Attivo'"
        righe = execute_query(conn, query)
        return [r[0] for r in righe]

    cliente_dict["intolleranze"] = fetch_lista("IntolleranzaAlimentare", "intolleranza")
    cliente_dict["condizioni_pregresse"] = fetch_lista("CondizioniPatologichePregresse", "condizione_preg")
    cliente_dict["condizioni_familiari"] = fetch_lista("CondizioniPatologicheFamiliari", "condizione_fam")
    cliente_dict["farmaci"] = []  # TODO: crea tabella `Farmaco` se vuoi

    return cliente_dict


def modifica_cliente(data: dict):
    conn = _get_connection()

    def parse_list(l): return l if isinstance(l, list) else []


    update_password = ""
    if data.get("password"):
        password_criptata = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        update_password = f", password = '{password_criptata}'"

    # Query di update del cliente
    query = f"""
    UPDATE Cliente SET
        email = {format_value(data["email"])},
        indirizzo = {format_value(data.get("indirizzo"))},
        peso = {format_value(data.get("peso"))}
        {update_password}
    WHERE id = {data["client_id"]}
    """
    insert_data_query(conn, query)

    # Svuoto le liste attuali
    def delete_from(tabella):
        return insert_data_query(conn, f"DELETE FROM {tabella} WHERE id_cliente = {data['client_id']}")

    delete_from("IntolleranzaAlimentare")
    delete_from("CondizioniPatologichePregresse")
    delete_from("CondizioniPatologicheFamiliari")

    # Reinserisco le nuove
    def insert_lista(tabella, campo, valori):
        for v in valori:
            q = f"INSERT INTO {tabella}(id_cliente, {campo}, stato) VALUES ({data['client_id']}, {format_value(v)}, 'Attivo')"
            insert_data_query(conn, q)

    insert_lista("IntolleranzaAlimentare", "intolleranza", parse_list(data.get("intolleranze")))
    insert_lista("CondizioniPatologichePregresse", "condizione_preg", parse_list(data.get("condizioni_pregresse")))
    insert_lista("CondizioniPatologicheFamiliari", "condizione_fam", parse_list(data.get("condizioni_familiari")))

    return {"message": "Profilo aggiornato correttamente"}

#funzione per elimianre un appuntamento lato cliente
def elimina_appuntamento_logico(id_appuntamento: int):
    conn = _get_connection()
    try:
        # invio email di disdetta email
        cursor = conn.cursor()
        cursor.execute("SELECT Medico.email, Cliente.email, Appuntamento.data_appuntamento FROM Appuntamento join Medico on Appuntamento.id_medico = Medico.id join Cliente on Appuntamento.id_cliente = Cliente.id WHERE Appuntamento.id = ?", (id_appuntamento, ))
        medico_mail, cliente_mail, data_appuntamento = cursor.fetchall()[0]

        query = f"CALL elimina_appuntamento_logico({id_appuntamento})"
        execute_query(conn, query)

        # l'invio effettivo avviene dopo l'eliminazione così da non avere problemi di coerenza in caso di operazioni fallite
        send_appointment_cancellation(medico_mail, data_appuntamento)
        send_appointment_cancellation(cliente_mail, data_appuntamento)
        print("EMAIL DI DISDETTA INVIATE CON SUCCESSO LATO CLIENTE")

        return {"message": "Appuntamento eliminato logicamente con successo"}
    except Exception as e:
        print("Errore durante l'eliminazione logica dell'appuntamento:", e)
        raise HTTPException(status_code=500, detail="Errore nella cancellazione logica dell'appuntamento")

def get_appuntamenti_cliente(id_cliente: int):
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"CALL get_appuntamenti_cliente({id_cliente})")
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()

        appuntamenti = [dict(zip(column_names, row)) for row in result]

        # formattazione dell orario
       
        for appuntamento in appuntamenti:
            if "ora_appuntamento" in appuntamento:
                ora_val = appuntamento["ora_appuntamento"]

                if hasattr(ora_val, "strftime"):
                    appuntamento["ora_appuntamento"] = ora_val.strftime("%H:%M")
                elif isinstance(ora_val, (int, float)):
                    total_seconds = int(ora_val)
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    appuntamento["ora_appuntamento"] = f"{hours:02d}:{minutes:02d}"
                else:
                    appuntamento["ora_appuntamento"] = str(ora_val)

        return appuntamenti
    except Exception as e:
        print("Errore durante il recupero degli appuntamenti del cliente:", e)
        raise HTTPException(status_code=500, detail="Errore nel recupero degli appuntamenti")
