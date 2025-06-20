from fastapi import HTTPException, status
from database.chatting import *
from .virtual_assistant import VirtualMedicalAssistant
from backend.llm_interaction.sidetask import SideTaskClassifier
from database.geo import get_nearest_drs, create_map_html_file
from typing import Any
from backend.login_back_utenti.send_mail import booking_mail
from backend.llm_interaction.utilities import *
from config import OUT_OF_TASK_LIST_MSG
 


def llm_interact(client_id:int, chat_id: int, new_msg: str) -> str: 
    """
    - Fetch history if any relative to the requested chat;
    - Classify msg to select the task
    - Handle each possible task the assistant is said to answer
    Args:
        client_id (int): 
        chat_id (int): 
        new_msg (str): 

    Raises:
        HTTPException: 

    Returns:
        str: llm answer
    """

    print(f"Entra con successo nella funzione di interazione con id = {client_id} e chat_id = {chat_id}")

    try:
        history = fetch_existing_chat_history(client_id, chat_id)
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "ERRORE: non esiste la tabella cercata, non dovresti poter fare questa chiamata, solo NEW")
    
    vma = VirtualMedicalAssistant(history)
    # getting and cleaning the classification msg
    classified_task = vma.classify_task(new_msg).strip().lower()
    if '"' in classified_task:
        classified_task = classified_task.replace('"', '')
    if "'" in classified_task:
        classified_task = classified_task.replace("'", "")
    print("La frase è stata classificata come: ", classified_task)

    # TODO: scegliere se quando la frase non ha senso printare un messaggio fisso [+efficiente, -umano] o far dire all'LLM le sue mansioni
    result = None
    if classified_task not in VirtualMedicalAssistant.TASK_LIST:
        print(f"Il messaggio non è stato recepito come un task che questo assistente può svolgere: <{classified_task}>")
    
    elif classified_task == vma.DESCRIPTION_TASK:
        result = handle_symptom_analysis(vma, client_id, chat_id, new_msg)

        specialization_classifier = SideTaskClassifier()
        specialization = specialization_classifier.classify_specialization(result)
        
        # TODO: capire se si vuole la possibilità di più output possibili
        
        print(f"Specializzazione/i scelta/e: {specialization}")
        if specialization.lower() != "nessuna":
            update_msg_with_suggested_field(client_id, chat_id, specialization)
            



    
    elif classified_task == vma.SEARCH_TASK:
        print("RICERCA SPECIALISTI RECEPITA")
        specializations = fetch_suggested_field(client_id, chat_id)
        if not specializations:
            return None
        result = handle_search(vma, specializations, client_id, chat_id, new_msg)
        print("Fine gestione ricerca")
    
    elif classified_task == vma.SEARCH_WITHOUT_DESCRIPTION:
        print("RICERCA SPECIALISTI SENZA DESCRIZIONE RECEPITA")
        sideTask = SideTaskClassifier()
        specialization = sideTask.extract_specialization_from_direct_request(new_msg)
        result = handle_search(vma, specialization, client_id, chat_id, new_msg)

    elif classified_task == vma.BOOKING_TASK_NO_DATE:
        print("PRENOTAZIONE VISITA SENZA DATA RECEPITA")
        result = handle_booking_without_date(vma, client_id, chat_id, new_msg)
        
    elif classified_task == vma.BOOKING_TASK_WITH_DATE:
        print("PRENOTAZIONE VISITA CON DATA RECEPITA")
        result = handle_booking_with_date(vma, client_id, chat_id, new_msg)

    else:
        result = OUT_OF_TASK_LIST_MSG

    return result



def handle_symptom_analysis(vma: VirtualMedicalAssistant, client_id: int, chat_id: int, new_msg: str):
    result = vma.analyze_symptoms(new_msg, build_clinical_support_sheet(client_id))
    print("Riultato in questo punto:")
    print(result)
    try:
        save_history(client_id, chat_id, vma.get_history()[-2]["content"], result[:result.rfind("[")])
    except Exception as e:
        print("Catturata eccezione: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
    return result

def handle_search(vma: VirtualMedicalAssistant, specialization: List[str], client_id: int, chat_id: int, new_msg: str) -> str:
    """
    genera le informazioni.
    opera con l'llm per rispondere con le informazioni
    """

    # TODO: integrare il sistema di ranking; potenzialmente o modificare la funzione get_nearest_drs, in modo che in quella lista vi siano le informazioni complete
    # oppure fare una funzione parallela e poi fare merge delle informazioni dei due sulla base dell'uguaglianza dei medici
    
    # dizionario con possibili chiavi i campi ottenuti, es. cardiologia, ortopedia;
    # ciasun campo è associato a una lista di dizionari in cui le chiavi sono campi utili per la posizione del medico, i valori sono i numeri corrispondenti (vedi docstring funzione fetch_drs_position_info)
    data:Dict[str, List[Dict[str, Any]]] = {}
    
    client_address = fetch_client_address(client_id)
    nearest_doc_by_field = get_nearest_drs(client_address, specialization)
    
    # TODO: questo codice si può semplificare se si considera come da dovere di poter avere una unica specializzazione indicata
    data[specialization] = nearest_doc_by_field

    try:
        create_temp_table_for_dynamic_booking(client_id, chat_id, nearest_doc_by_field)
    except Exception as e:
        print("Ecczione verificata durante la creazione della tabella temporanea: ", e, type(e))

    print("pre creazione mappa")
    create_map_html_file(client_address, nearest_doc_by_field, map_name=f"mappa_{specialization}")

    cleaned_data = {}
    #d: dict, l:list
    for d, l in data.items():
        cleaned_data[d] = [{k:v for k,v in el.items() if k not in ("id", "id_specializzazione", "latitudine", "longitudine")} for el in l]
    result = vma.handle_search(new_msg, cleaned_data)
    print("Pre salvataggio")
    try:
        save_history(client_id, chat_id, vma.get_history()[-2]["content"], result)
        print("Post salvataggio")
    except Exception as e:
        print("Catturata eccezione: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
    return result

def handle_booking_without_date(vma: VirtualMedicalAssistant, client_id: int, chat_id: int, new_msg: str) -> str:
    booking_classifier = SideTaskClassifier()
    field = fetch_suggested_field(client_id, chat_id)
    if not field:
        # caso in cui la conversazione parte con un "vorrei prenotare una visita con un ...[cardiologo]"
        field = booking_classifier.extract_specialization_from_direct_request(new_msg)
        """ if field == "nessuna":
            result = vma.ask_to_repeat() """
    print(f"Field = {field}")
    data:Dict[str, List[Dict[str, Any]]] = {}

    # reupera info sui medici vicini di quella categoria
    client_address = fetch_client_address(client_id)
    nearest_doc_by_field = get_nearest_drs(client_address, field)

    # flow di prenotazione
    full_name = booking_classifier.classify_booking_with_or_without_name(new_msg).strip()
    print(f"Nome trovato = {full_name}")
    if full_name.lower() == 'non indicato':
        # proporre una lista e chiedere di eplicitare il nome e il cognome con cui vuole prenotare
        data[field] = [{key: value for key, value in nearest_single_doc_by_field.items() if key not in ("id", "id_specializzazione", "latitudine", "longitudine")} for nearest_single_doc_by_field in nearest_doc_by_field]
        result = vma.ask_for_booking_without_name(new_msg, data)
        
        
    else:
        name, surname = estrai_nome_cognome(full_name) 
        print("Estratti:", name, surname)

        # fissare un appuntamento
        selected_doc = None
        # se ci sono cerca tra i vari medici, altrimenti potrebbe essere stato specificato solo il nome del medico 
        if nearest_doc_by_field:
            for doc in nearest_doc_by_field:
                if doc["nome"].lower() == name.lower() and doc["cognome"].lower() == surname.lower():
                    selected_doc = doc
        else: 
            # TODO: trattare il caso di omonimia
            selected_doc = get_doc_by_full_name(name, surname)[0]

        if selected_doc:
            update_msg_with_selected_doc(client_id, chat_id, selected_doc["id"])

        # TODO: andrebbero trovati gli slot di tempo liberi del dottore

        # per il db il formato dei timestamp è --'AAAA-MM-GG HH:MM:SS'
        result = vma.ask_for_booking_date(new_msg, selected_doc)

    try:
        save_history(client_id, chat_id, vma.get_history()[-2]["content"], result)
    except Exception as e:
        print("Catturata eccezione: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
       
    return result


def handle_booking_with_date(vma: VirtualMedicalAssistant, client_id: int, chat_id: int, new_msg: str):
    result = None
    correct_format_date_agent = SideTaskClassifier()
    date = correct_format_date_agent.correct_date_format(new_msg)
    print(f"Data estratta: {date}")
    if date.lower() != "non indicato":
        with get_cursor() as cursor:
            cursor: mariadb.Cursor
            doc = fetch_selected_doc(client_id, chat_id)
            doc_id = doc["id"]
            cursor.callproc("prenota_appuntamento", [client_id, doc_id, date])
    
            # Questo serve a leggere il risultato della SELECT finale
            consume_procedure_result(cursor)
            
            result = f"Appuntamento confermato, invio email di conferma a lei e al dr./dr.essa {doc['nome']} {doc['cognome']}"
            
            doc_mail = doc["email"]
            address = doc["indirizzo"]
            doc_name = doc["nome"]
            doc_surname = doc["cognome"]
            phone = doc["telefono"] if doc["telefono"] else None
            client_info = fetch_client_info(client_id)
            client_mail = client_info["email"]
            client_name = client_info["nome"]
            client_surname = client_info["cognome"]
            booking_mail(client_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)
            booking_mail(doc_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)

        try:
            save_history(client_id, chat_id, vma.get_history()[-2]["content"], result)
        except Exception as e:
            print("Catturata eccezione: ", e, type (e))
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
        
        return result

    else:
        raise Exception("Se arriva qui vuol dire che ha classificato per data un testo che non contiene alcuna indicazione temporale...")
