import mariadb
from .database import get_cursor
from typing import List, Dict, Any
import json
from backend.llm_interaction.virtual_assistant import VirtualMedicalAssistant

def save_history(client_id: int, chat_id: int, llm_question: str, answer: str):
    """
    Save a new message in the database.
    Args:
        client_id (int): 
        chat_id (int): 
        llm_question (str): this string should be the full prompt, not only the message to keep track of every bit of information
        answer (str): this string should be the answer from the llm without non-conversational information
    """
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT reparti_consigliati, id_medico FROM messaggi_{client_id}_{chat_id} where id = (SELECT MAX(id) FROM messaggi_{client_id}_{chat_id})")
        result = cursor.fetchall()
        last_response = result[0][0] if result else None
        doc_id = result[0][1] if result else None
        cursor.execute(f"INSERT INTO messaggi_{client_id}_{chat_id} (domanda, risposta, reparti_consigliati, id_medico) VALUES (?, ?, ?, ?)", (llm_question, answer, last_response, doc_id))

def create_chat_and_msg_tables(client_id: int) -> int:
    """
    Create a new chat, handling the database as follows:
    - create a new entry for Chat 
    - create relative new table to store messages
    Then iniziliatizes the chat with proper instructions to the LLM
    Args:
        client_id (int):
    Raises:
        Exception: database connection issues or msg len error to store in the db
    Returns:
        int: chat id, on success
    """
    chat_id = -1
    try:
        with get_cursor() as cursor:
            cursor: mariadb.Cursor
            # crea una chat
            cursor.execute(f"INSERT INTO Chat (id_cliente, stato) VALUES (?, 'Attivo')", (client_id,))  # DATA must be tuple/list
            chat_id = cursor.lastrowid
            # crea una storia per la chat
            cursor.execute(f"CREATE TABLE IF NOT EXISTS messaggi_{client_id}_{chat_id} (\
                        id INT AUTO_INCREMENT,\
                        domanda VARCHAR(2000),\
                        risposta VARCHAR(2000),\
                        reparti_consigliati VARCHAR(255) DEFAULT NULL,\
                        id_medico INT DEFAULT NULL,\
                        constraint pk_messaggi_{client_id}_{chat_id} primary key (id),\
                        constraint fk_messaggi_{client_id}_{chat_id}_medico FOREIGN KEY (id_medico) REFERENCES Medico(id)\
                        )")
            vma = VirtualMedicalAssistant()
            initializaiton_history = vma.get_history()
            save_history(client_id, chat_id, initializaiton_history[0]["content"], initializaiton_history[1]["content"])
            print("Assistente virutale inizializzato...")
    except Exception as e:
        print("Catturata eccezione: ", e, type(e))
        with get_cursor() as cur:
            cur: mariadb.Cursor
            cur.execute(f"DROP TABLE IF EXISTS messaggi_{client_id}_{chat_id}")
            cur.execute(f"DELETE FROM Chat where id = ?", (chat_id, ))
            print("Operazioni di cleanup sulla creazione chat fallita eseguite")
    if chat_id:
        return chat_id  
    else:
        raise Exception("Assitente virtuale non inizializzato correttamente")


def fetch_all_chats_for_client(client_id: int) -> List[int]:
    """Returns the list of ids of all chat associated with a user, both active and not"""
    result = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT id FROM Chat WHERE id_cliente = ?", (client_id, ))
        res = cursor.fetchall() # lista del tipo [(id1, ), (id2, )...]
        for item in res:
            result.append(item[0])
    return result


def fetch_existing_chat_history(client_id: int, chat_id: int) -> List[Dict[str, str]]:
    history = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute("SELECT * FROM Chat WHERE id = ? and id_cliente = ?", (chat_id, client_id))
        result = cursor.fetchall()
        
        if not result:
            raise Exception("Tabella non trovata")
        cursor.execute(f"SELECT domanda, risposta FROM messaggi_{client_id}_{chat_id}")    # List[Tuple]
        result = cursor.fetchall()
        
        for question, answer in result:
            history.append({
                "role":"user",
                "content": question
            })
            history.append({
                "role":"assistant",
                "content": answer
            })
    return history


def fetch_db_pure_chat(client_id: int, chat_id: int) -> List[Dict[str, str]]:
    pure_chat = []
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT domanda, risposta FROM messaggi_{client_id}_{chat_id} where id > 1")  # scarta la prima, è di inizializzazione
        # [(domanda1, risposta1), (d2,r2)...]
        result = cursor.fetchall()
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
        print("Eccezione durante l'estrazione del prompt puro: ", e, type(e))
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


def update_msg_with_suggested_field(client_id: int, chat_id: int, specializations: List[str]):
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        # seleziono dall'ultimo messaggio inserito perché è l'informazione più aggiornata possibile
        cursor.execute(f"UPDATE messaggi_{client_id}_{chat_id} SET reparti_consigliati = ? WHERE id = (SELECT MAX(id) FROM messaggi_{client_id}_{chat_id})", (specializations,))
    print("Aggiornato lo specialista consigliato al messaggio corrente")

def update_msg_with_selected_doc(client_id:int, chat_id: int, doc_id: int):
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"UPDATE messaggi_{client_id}_{chat_id}\
                       SET id_medico = ?\
                       WHERE id = (SELECT MAX(id) FROM messaggi_{client_id}_{chat_id})", (doc_id,))
    print("Aggiornato il medico con cui si vuole fare la prenotazione")


def fetch_suggested_field(client_id, chat_id) -> List[str]:
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT reparti_consigliati FROM messaggi_{client_id}_{chat_id} WHERE id = (SELECT MAX(id) FROM messaggi_{client_id}_{chat_id})")
        result = cursor.fetchall()
    if result is not None:
        print("Recuperato da db campo suggerito: ", result)
        result = result[0][0]
    return result


def fetch_client_address(client_id: int):
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT indirizzo FROM Cliente where id = ?", (client_id, ))
        result = cursor.fetchall()
    return result


def fetch_selected_doc(client_id:int, chat_id: int) -> Dict[str, Any]:
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"SELECT id_medico FROM messaggi_{client_id}_{chat_id}\
                       WHERE id = (SELECT MAX(id) FROM messaggi_{client_id}_{chat_id})")
        result = cursor.fetchall()[0][0]
        print(f"Id medico reperito = {result}")
        if result:
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
        else:
            return None

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
        
def get_doc_by_full_name(doc_name: str, doc_surname: str) -> List[Dict[str, Any]]:
    result = []
    with get_cursor() as cursor:
        cursor:mariadb.Cursor
        print("ATTENZIONE IN get_specific_doc: NON è SICURA IN CASI DI OMONIMIA, NON è PENSATA PER TRATTARLI")
        cursor.execute("SELECT Medico.id, nome, cognome, email, telefono, url_sito, specializzazione, Medico.indirizzo FROM Medico join Specializzazione on Medico.id = id_medico WHERE Medico.nome = ? and Medico.cognome = ?", (doc_name, doc_surname))
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



def create_temp_table_for_dynamic_booking(client_id: int, chat_id: int, nearest_doc_by_field:List[Dict[str, Any]]) -> None:
    """Responsible for automatic creation of the temp_{client_id}_{chat_id} tables used in dynamic side booking system"""
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.execute(f"DROP TABLE IF EXISTS temp_{client_id}_{chat_id}")
        cursor.execute(f"""CREATE TABLE temp_{client_id}_{chat_id} 
                       (
                       id INT PRIMARY KEY AUTO_INCREMENT,
                       id_medico INT REFERENCES Medico(id), 
                       nome VARCHAR(40),
                       cognome VARCHAR(40), 
                       specializzazione VARCHAR(255), 
                       indirizzo VARCHAR(255), 
                       distanza_km DECIMAL(10,7)
                       )""")
        query = f"""
            INSERT INTO temp_{client_id}_{chat_id} (id_medico, nome, cognome, specializzazione, indirizzo, distanza_km)
            VALUES (%(id)s, %(nome)s, %(cognome)s, %(specializzazione)s, %(indirizzo)s, %(distanza_km)s)
        """
        for doc in nearest_doc_by_field:
            cursor.execute(query, doc)
    
