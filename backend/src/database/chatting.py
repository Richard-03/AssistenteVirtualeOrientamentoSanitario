import mariadb
from .database import get_cursor
from typing import List, Dict, Any
import json
from backend.llm_interaction.utilities import consume_procedure_result

def save_history(client_id: int, chat_number: int, llm_question: str, answer: str, suggested_field:str = None, suggested_doc_id:int = None) -> None:
    """Save a new message in the database. Also keeps updated the sidebar."""

    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        print("IL NUOVO #CHAT è ", chat_number)
        cursor.execute(f"SELECT reparto_consigliato, id_medico FROM Chat where id_cliente = ? and numero_chat = ?", (client_id, chat_number))
        result = cursor.fetchall()
        last_response = result[0][0] if result else None
        last_doc_id = result[0][1] if result else None

        response = suggested_field.title() if suggested_field else last_response
        doc_id = suggested_doc_id if suggested_doc_id else last_doc_id

        if chat_number != 0:
            cursor.callproc("update_chat", (client_id, chat_number, llm_question, answer, response, doc_id))
        else:
            cursor.callproc("insert_chat", (client_id, llm_question, answer, response, doc_id))
        consume_procedure_result(cursor)


# TODO: ELIMINARE
#        if response:
#            _update_sidebar_table(client_id, chat_number, response)

""" 
def _update_sidebar_table(client_id:int, chat_number:int, specialization: str) -> None:
    print("Aggiornamento tabella per sidebar in parallelo al salvataggio...")
    with get_cursor() as cursor:
        cursor:mariadb.Cursor
        currently_possible_docs = fetch_specialists(specialization)
        for doc in currently_possible_docs:
            doc_id = doc["id"]
            cursor.execute("SELECT doc_id FROM MedicoSuggerito where id_cliente = ? and id_chat = ?", (client_id, chat_number))
            result = cursor.fetchall()
            if result:
                last = 
            cursor.callproc("insert_medico_suggerito", (client_id, chat_number, doc_id))
            consume_procedure_result(cursor)
    print("Fine ggiornamento tabella per sidebar in parallelo al salvataggio") """


def fetch_all_chats_for_client(client_id: int) -> List[int]:
    """Returns the list of ids of all active chats associated with a user"""
    result = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT DISTINCT numero_chat FROM Chat WHERE id_cliente = ? and stato = 'Attivo' ORDER BY id", (client_id, ))
        res = cursor.fetchall() # lista del tipo [(id1, ), (id2, )...]
        for item in res:
            result.append(item[0])
    return result


def fetch_existing_chat_history(client_id: int, chat_number: int) -> List[Dict[str, str]]:
    history = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT domanda, risposta FROM Chat WHERE numero_chat = ? and id_cliente = ? ORDER BY id", (chat_number, client_id))
        result = cursor.fetchall()

        if result:
            # se esiste bisogna processare il saluto in maniera diversa
                            
            hellomsg = result[0][0]    # del tipo domanda = INIT, risposta = NULL
            history.append({
                "role": "system",
                "content": hellomsg
            })

            result = result[1:]

            for question, answer in result:
                history.append({
                    "role":"user",
                    "content": question
                })
                history.append({
                    "role":"assistant",
                    "content": answer
                })
        else:
            print("NESSUNA STORIA DA RECUPERARE NELLA FETCH EXISTING CHAT HISORY")
    return history


def get_last_chat_number(client_id: int) -> int:
    ret = 0
    with get_cursor() as cursor:
        cursor:mariadb.Cursor
        cursor.execute("SELECT numero_chat from Chat where id_cliente = ?", (client_id, ))
        result = cursor.fetchall()
        if result:
            ret = result[-1][0]
            print(f"Recupero ultimo numero di chat associata a un utente: {ret}")
        else:
            print("Non ci sono risultati, quindi non ci sono chat iniziate dall'utente")
    return ret


def fetch_db_pure_chat(client_id: int, chat_number: int) -> List[Dict[str, str]]:
    """Pure chat means only msg written by user without any wrapper used in the prompt to instruct the assitant.
        Returns a structure in the form [{"sender": "AI"/"utente", "text": "example"}]"""

    pure_chat = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT domanda, risposta FROM Chat where numero_chat = ? and id_cliente = ? ORDER BY id", (chat_number, client_id))  
        # [(domanda1, risposta1), (d2,r2)...]
        result = cursor.fetchall()

        if result:    
            # chat già inizializzata, bisogna scartare l'inizializzazione
            pure_chat.append({"sender": "AI", "text": result[1][1]})
            result = result[2:]

        for t in result:
            qa = {}
            qa["sender"] = "utente"
            pure_text = _get_pure_text(t[0])# surrogato di t[0]
            qa["text"] = pure_text if pure_text != "" else t[0]
            pure_chat.append(qa)
            qa = {}
            qa["sender"] = "AI"
            qa["text"] = t[1]
            pure_chat.append(qa)
    return pure_chat

def _get_pure_text(testo_con_tripli_apici: str):
    "Input text should be in the form 'start + '''text''' + end'. Returns '' if something goes wrong"
    try:
        sections = testo_con_tripli_apici.split("'''")
        ret = sections[1]
        return ret.strip()
    except Exception as e:
        print("Eccezione durante l'estrazione del prompt puro (Out of Range previsto solo per i primi 2 messaggi di inizializzazione): ", e, type(e))
        return ""


def build_clinical_support_sheet(client_id: int) -> str:
    """
    Returns:
        str: data sheet of the client, in json format:
        - eta
        - altezza
        - peso
        - sesso
        - intolleranze
        - condizioni_patologiche_familiari
        - condizioni_patologiche_pregresse
    """
    data_sheet = None
    with get_cursor() as cursor:
        cursor:mariadb.Cursor
        cursor.execute('SELECT eta, sesso, peso, altezza, intolleranza, condizione_patologica_familiare, condizione_patologica_pregressa FROM view_dati_cliente_attivo where id_cliente = ?', (client_id, ))
        result = cursor.fetchall()
        intolerances = set()
        fam_conds = set()
        pre_conds = set()
        age, gender, weight, height = result[0][:4]
        print(age, gender, weight, height)

        for _,_,_,_, intolerance, fam_cond, pre_cond in result:
            if intolerance is not None:
                intolerances.add(intolerance)
            if fam_cond is not None:
                fam_conds.add(fam_cond)
            if pre_cond is not None:
                pre_conds.add(pre_cond)
        data_sheet = {
            "eta": age,
            "altezza": float(height),   # height -- Decimal(value) --> cast --> value
            "peso": float(weight),      # weight -- Decimal(value) --> cast --> value
            "sesso": "maschio" if gender.lower() == 'm' else "femmina",
            "intolleranze": list(intolerances),
            "condizioni_patologiche_familiari": list(fam_conds),
            "condizioni_patologiche_pregresse": list(pre_conds)
        }
    return json.dumps(data_sheet, ensure_ascii=False)


def fetch_specialists(specialization: str) -> List[Dict[str, str]]:
    """
    Get *all* infos searching by specialization. 
    Assumption: title_case for field in the db
    Args:
        specialization (str): 
    Returns:
        List[Dict[str, str]]: json-like representation of result 
    """
    result = None
    specialization = specialization.title()
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT * FROM Medico LEFT JOIN Specializzazione ON Medico.id = Specializzazione.id_medico where Specializzazione.specializzazione = ?", (specialization,))
        result = cursor.fetchall()
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'user_db' AND TABLE_NAME = 'Medico'")
        cols = cursor.fetchall()
        result = [{cols[i][0]: result[j][i] for i in range(1, len(cols[0]))} for j in range(len(result))]
    return result




def fetch_suggested_field(client_id: int, chat_number: int) -> str:
    """Fetch the specialization saved in the db as last considered in the chat. Returns None if there isn't."""
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT reparto_consigliato FROM Chat WHERE id_cliente = ? and numero_chat = ? ORDER BY id", (client_id, chat_number))
        response = cursor.fetchall()
    if response:
        print("Recuperato da db campo suggerito: ", response)
        result = response[-1][0]
        print("Quindi restituito: ", result)
    return result


def fetch_client_address(client_id: int):
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT indirizzo FROM Cliente where id = ?", (client_id, ))
        result = cursor.fetchall()
    return result


def fetch_selected_doc(client_id:int, chat_number: int) -> Dict[str, Any]:
    doc = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT DISTINCT id_medico FROM Chat where id_cliente = ? and numero_chat = ? and id_medico is not NULL ORDER BY id", (client_id, chat_number))
        result = cursor.fetchall()
        if result:
            # se c'è, interessa l'ultimo medico accordato con il cliente
            result = result[-1][0]
            print(f"Id medico reperito = {result}")
            # TODO: Medico.indirizzo preso, invece dell'indirizzo specifico di ciascuna specializzazione associata al medico
            cursor.execute("SELECT Medico.id, nome, cognome, email, telefono, url_sito, specializzazione, Medico.indirizzo FROM Medico join Specializzazione on Medico.id = id_medico WHERE Medico.id = ?", (result,))
            result = cursor.fetchall()[0]
            doc = {
                "id": result[0],
                "nome": result[1],
                "cognome": result[2],
                "email": result[3],
                "telefono": result[4],
                "sito":  result[5],
                "specializzazione": result[6],
                "indirizzo": result[7]
            }
        return doc

def fetch_client_info(client_id: int) -> Dict:
    client_data = {}
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT nome, cognome, indirizzo, email FROM Cliente WHERE id = ?", (client_id, ))
        # lista di tuple (1 sola) di campi
        result = cursor.fetchall()[0]
    if result:
        client_data["nome"], client_data["cognome"], client_data["indirizzo"], client_data["email"] = result
    return client_data
        
def get_doc_by_full_name_and_field(doc_name: str, doc_surname: str, field:str) -> List[Dict[str, Any]]:
    result = []
    with get_cursor() as cursor:
        cursor:mariadb.Cursor
        print("ATTENZIONE IN get_specific_doc: NON è SICURA IN CASI DI OMONIMIA, NON è PENSATA PER TRATTARLI")
        cursor.execute("SELECT Medico.id, nome, cognome, email, telefono, url_sito, specializzazione, Medico.indirizzo FROM Medico join Specializzazione on Medico.id = id_medico WHERE Medico.nome = ? and Medico.cognome = ? and Specializzazione.specializzazione = ?", (doc_name, doc_surname, field))
        response_list = cursor.fetchall()
        for response in response_list:
            doc = {
                "id": response[0],
                "nome": response[1],
                "cognome": response[2],
                "email": response[3],
                "telefono": response[4],
                "sito":  response[5],
                "specializzazione": response[6],
                "indirizzo": response[7]
            }
        result.append(doc)
        print("ritorna con successo uno o più dottori")
    return result
