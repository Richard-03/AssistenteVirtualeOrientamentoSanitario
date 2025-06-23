from fastapi import HTTPException, status
from database.chatting import *
from .virtual_assistant import VirtualMedicalAssistant
from backend.llm_interaction.sidetask import SideTaskClassifier
from database.geo import get_nearest_drs, create_map_html_file
from typing import Any, Optional
from backend.login_back_utenti.send_mail import booking_mail
from backend.llm_interaction.utilities import *
 
""" 

homonymy_doc_list_global: List[Dict[str, Any]] = []
homonymy_trigger_msg_global:str = None """


def init_vma(client_id:int, chat_number:int) -> None:
    """Initialize the Assitant to have hello msg displayed"""
    # salvataggio dell'inizializzazione
    vma = VirtualMedicalAssistant()
    history = vma.get_history()
    try:
        save_history(client_id, chat_number, history[0]["content"], None)
        save_history(client_id, chat_number, history[1]["content"], history[2]["content"])
    except Exception as e:
        print("Impossibile salvare la storia dell'inizializzazione: ", e, type(e))
        raise

def llm_interact(client_id:int, chat_number: int, new_msg: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> str: 
    """
    - Fetch history if any relative to the requested chat;
    - Classify msg to select the task
    - Handle each possible task the assistant is said to answer
    Returns:
        str: llm answer
    """

    print(f"Entra con successo nella funzione di interazione con id_cliente = {client_id} e numero_chat = {chat_number}")
    history = []
    try:
        history = fetch_existing_chat_history(client_id, chat_number)
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "ERRORE: non esiste la tabella cercata, non dovresti poter fare questa chiamata, solo NEW")
    
    vma = VirtualMedicalAssistant(history)
    
    # getting and cleaning the classification msg
    classified_task = vma.classify_task(new_msg)
    print("La frase è stata classificata come: ", classified_task)

    result = None
    if classified_task not in VirtualMedicalAssistant.TASK_LIST:
        print(f"Il messaggio non è stato recepito come un task che questo assistente può svolgere: <{classified_task}>")
    
    elif classified_task == vma.DESCRIPTION_TASK:
        result = handle_symptom_analysis(vma, client_id, chat_number, new_msg)
            
    elif classified_task == vma.SEARCH_TASK:
        print("RICERCA SPECIALISTI RECEPITA")
        specialization = fetch_suggested_field(client_id, chat_number)
        if not specialization:
            result = vma.ask_more(new_msg)
            try:
                save_history(client_id, chat_number, vma.get_history()[-2]["content"], result)
            except Exception as e:
                print("Catturata eccezione in: handle_symptom_analysis | interaction.py: ", e, type (e))
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
        
        else:
            # questa classificazione è per robustezza: può acccadere che il modello restituica più di un campo e la classificazione invece di dire
            sideTask = SideTaskClassifier()
            other_specialization = sideTask.extract_specialization_from_direct_request(new_msg)
            if other_specialization.lower() != specialization.lower() and other_specialization != "nessuna":
                specialization = other_specialization
            result = handle_search(vma, specialization, client_id, chat_number, new_msg, latitude, longitude)
        print("Fine gestione ricerca")
    
    elif classified_task == vma.SEARCH_WITHOUT_DESCRIPTION:
        print("RICERCA SPECIALISTI SENZA DESCRIZIONE RECEPITA")
        # nel caso la chat inizi con la richiesta di un medico senza aver mai parlato dei sintomi prima
        sideTask = SideTaskClassifier()
        specialization = sideTask.extract_specialization_from_direct_request(new_msg)
        if specialization.lower() == "nessuna":
            print("RICHIESTA DI MAGGIORI INFO DA PARTE DELL'LLM")
            result = vma.ask_more(new_msg)
            try:
                save_history(client_id, chat_number, vma.get_history()[-2]["content"], result)
            except Exception as e:
                print("Catturata eccezione in: handle_symptom_analysis | interaction.py: ", e, type (e))
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
        
        else:
            result = handle_search(vma, specialization, client_id, chat_number, new_msg, latitude, longitude)

    elif classified_task == vma.BOOKING_TASK_NO_DATE:
        print("PRENOTAZIONE VISITA SENZA DATA RECEPITA")
        result = handle_booking_without_date(vma, client_id, chat_number, new_msg, latitude, longitude)
        
    elif classified_task == vma.BOOKING_TASK_WITH_DATE:
        print("PRENOTAZIONE VISITA CON DATA RECEPITA")
        result = handle_booking_with_date(vma, client_id, chat_number, new_msg)


    else:
        result = vma.tell_task(new_msg)
        try:
            save_history(client_id, chat_number, vma.get_history()[-2]["content"], result, suggested_field = specialization if specialization != "nessuna" else None)
        except Exception as e:
            print("Catturata eccezione in: handle_symptom_analysis | interaction.py: ", e, type (e))
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
    

    result = clean_string(result)
    return result



def handle_symptom_analysis(vma: VirtualMedicalAssistant, client_id: int, chat_number: int, new_msg: str):
    result = vma.analyze_symptoms(new_msg, build_clinical_support_sheet(client_id))
    specialization_classifier = SideTaskClassifier()
    specialization = specialization_classifier.classify_specialization(result)
    try:
        save_history(client_id, chat_number, vma.get_history()[-2]["content"], result, suggested_field = specialization if specialization != "nessuna" else None)
    except Exception as e:
        print("Catturata eccezione in: handle_symptom_analysis | interaction.py: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
    return result

def handle_search(vma: VirtualMedicalAssistant, specialization: str, client_id: int, chat_number: int, new_msg: str, latitude: Optional[float], longitude: Optional[float]) -> str:
    """
    genera le informazioni.
    opera con l'llm per rispondere con le informazioni
    """

    # ASSUMIAMO DI AVERE 1 SPECIALIZZAZIONE IN QUESTO PUNTO


    # TODO: integrare il sistema di ranking; potenzialmente o modificare la funzione get_nearest_drs, in modo che in quella lista vi siano le informazioni complete
    # oppure fare una funzione parallela e poi fare merge delle informazioni dei due sulla base dell'uguaglianza dei medici
    
    # recupero dei medici più vicini
    client_address = fetch_client_address(client_id)

    print(f"\nLATITUDINE E LONGITUDINE = ({latitude},{longitude})\n")
    nearest_docs_by_field = get_nearest_drs(client_address, specialization, latitude, longitude)

    create_map_html_file(client_address, nearest_docs_by_field, latitude, longitude, map_name=f"mappa_{specialization}")

    # selezione delle info utili e ottenimento della risposta dall'assistente
    cleaned_data = [{k:v for k,v in doc.items() if k not in ("id", "id_specializzazione", "latitudine", "longitudine")} for doc in nearest_docs_by_field]
    result = vma.handle_search(new_msg, cleaned_data)

    try:
        # salvo il messaggio con il contorno del prompt perché si tratta del contesto del'LLM
        # la tabella che serve per mantenere aggiornata la sidebar viene aggionrata in parallelo alla storia
        save_history(client_id, chat_number, vma.get_history()[-2]["content"], result, suggested_field=specialization)
    except Exception as e:
        print("Catturata eccezione: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
    return result

def handle_booking_without_date(vma: VirtualMedicalAssistant, client_id: int, chat_number: int, new_msg: str,  latitude: Optional[float], longitude: Optional[float]) -> str:
    # il campo o c'è già per conversazione pregressa (caso con o senza nome) o è esplicitato nel messaggio (caso senza nome)
    booking_classifier = SideTaskClassifier()
    field = fetch_suggested_field(client_id, chat_number)
    result = None
    selected_doc = None
    if not field:
        # caso in cui la conversazione parte con un "vorrei prenotare una visita con un ...[cardiologo]"
        # analogo a handle_search senza informazioni, cambia la forma verbale "vorrei prenotare..." | "mi fai vedere..."
        field = booking_classifier.extract_specialization_from_direct_request(new_msg)
        # assicuro formattazione utile per il seguito
        if field.lower() == "non indicato":
            # CASO STRANO: es. "vorrei prenotare una visita" come primo messaggio  
            print("ARRIVATI IN UN CASO STRANO DA HANDLE_BOOKING_WITHOUT_DATE")
            result = vma.ask_more(new_msg)
    else:
        # reupera info sui medici vicini di quella categoria
        client_address = fetch_client_address(client_id)
        nearest_docs_by_field = get_nearest_drs(client_address, field, latitude, longitude) if field != "non indicato" else []

        # vorrei prenotare ... 1) con un cardiologo/neurologo/... 2) con Nome Cognome
        full_name = booking_classifier.classify_booking_with_or_without_name(new_msg)
        print(f"Nome trovato = {full_name}")
        if full_name.lower() == 'non indicato':
            # proporre una lista e chiedere di eplicitare il nome e il cognome con cui vuole prenotare
            cleaned_data = [{k:v for k,v in doc.items() if k not in ("id", "id_specializzazione", "latitudine", "longitudine")} for doc in nearest_docs_by_field]
            result = vma.ask_for_booking_without_name(new_msg, cleaned_data)
             
        else:
            name, surname = estrai_nome_cognome(full_name) 
            print("Estratti:", name, surname)

            # non dovrebbe servire questo controllo per come è scritto il prompt
            if not name or not surname:
                result = vma.ask_better_name(new_msg)
                
            else:
                # fissare un appuntamento
                # LISTA per gestire l'omonimia, non è impossibile che 2 medici abbiano lo stesso nome e la stessa specializzazione
                selected_docs:List[Dict[str, Any]] = []
                # se ci sono cerca tra i vari medici, altrimenti potrebbe essere stato specificato solo il nome del medico 
                if nearest_docs_by_field:
                    for doc in nearest_docs_by_field:
                        if doc["nome"].lower() == name.lower() and doc["cognome"].lower() == surname.lower():
                            selected_docs.append(doc)

                else: 
                    # TODO: è DAVVERO UTILE QUESTO PEZZO?
                    print("ENTRO IN UN PEZZO DI DUBBIA UTILITà")
                    # CASO STRANO: viene passato direttamente un nome e un cognome
                    selected_docs = get_doc_by_full_name_and_field(name, surname, field)

                # TODO: trattare il caso di omonimia
                if len(selected_docs) == 1:
                    selected_doc = selected_docs[0]
                    # TODO: andrebbero trovati gli slot di tempo liberi del dottore
                    # TODO: RECUPERARE INFORMAZIONI DAL DB
                    # TODO: FORMATTARLE
                    # TODO: FORNIRLE ALL'LLM NELLA FUNZIONE CHE SEGUE

                    # per il db il formato dei timestamp è --'AAAA-MM-GG HH:MM:SS'
                    # selected_doc è passato per far riepilogare le informazioni
                    # TODO: INFO PASSATE PER GLI SLOT TEMPORALI




                    result = vma.ask_for_booking_date(new_msg, selected_doc)
                
                elif len(selected_docs) == 0:
                    result = vma.ask_better_name(new_msg)

                

                else:
                    # in qeusto branch viene trattata l'omonimia: da qui il msg viene salvato con field specificato e suggested_doc = NULL perché situazione di indecisione
                    out_list:List[str] = []
                    for i in range(len(selected_docs)):
                        out_list.append(f"{i+1}. {selected_docs[i]['nome']}, {selected_docs[i]['cognome']}, {selected_docs[i]['indirizzo']}")

                    static_anwer = "Ops, ci troviamo in un caso di omonimia, per favore usa la barra laterale per procedere alla prenotazione."

                    # la risposta ottenuta è in realtà pre-scritta
                    result = vma.handle_static_answer(new_msg, static_anwer)

    try:        
        save_history(client_id, chat_number, vma.get_history()[-2]["content"], result, suggested_field = field if field else None, suggested_doc_id = selected_doc["id"] if selected_doc else None)
    except Exception as e:
        print("Catturata eccezione: ", e, type (e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
       
    return result


def handle_booking_with_date(vma: VirtualMedicalAssistant, client_id: int, chat_number: int, new_msg: str):
    result = None
    print(f"Valore inizilizzato result = {result}")
    field = None
    doc_id = None
    correct_format_date_agent = SideTaskClassifier()
    date = correct_format_date_agent.correct_date_format(new_msg)
    print(f"Data estratta: {date} di tipo {type(date)}")
    if date.lower() != "non indicato":
        print("Entro con indicazione temporale")
        with get_cursor() as cursor:
            cursor: mariadb.Cursor
            doc = fetch_selected_doc(client_id, chat_number)
            print(f"Valore atteso = NULL, result = {result}")
            if not doc:
                field = fetch_suggested_field(client_id, chat_number)
                if field:
                    result = vma.ask_for_doc(new_msg)
                else:
                    # TODO: CASO STRANO, IN CUI VIENE CHIESTA UNA DATA MA SENZA MEDICO E SENZA CAMPO, es. "vorrei prenotare il 22/10/2025" in apertura, improbabileper questa applicazione
                    print("ARRIVATI IN UN CASO STRANO DA HANDLE_BOOKING_WITH_DATE")
                    result = vma.ask_to_repeat(new_msg)
            else:
                print(f"Valore atteso ramo else se indicato = NULL, result = {result}")

                doc_id = doc["id"]

                # TODO: LA PRENOTAZIONE DELL'APPUNTAMENTO LA LASCIO COSì O LA DELEGO A BOOKING MAIL? CODICE RIUTILIZZABILE DA GABRIELE?
                cursor.callproc("prenota_appuntamento", [client_id, doc_id, date])
        
                # Questo serve a leggere il risultato della SELECT finale
                consume_procedure_result(cursor)
                
                static_answer = f"Appuntamento confermato, inviata email di conferma a lei e al dr./dr.essa {doc['nome']} {doc['cognome']}"
                
                # messaggio fisso, aggiorno la chat come se fosse dell'assistente
                result = vma.handle_static_answer(new_msg, static_answer)


                doc_mail = doc["email"]
                address = doc["indirizzo"]
                doc_name = doc["nome"]
                doc_surname = doc["cognome"]
                phone = doc["telefono"] 
                client_info = fetch_client_info(client_id)
                client_mail = client_info["email"]
                client_name = client_info["nome"]
                client_surname = client_info["cognome"]
                booking_mail(client_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)
                booking_mail(doc_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)

        try:
            print(f"Valore atteso = True, bool(result) = {bool(result)}")

            save_history(client_id, chat_number, vma.get_history()[-2]["content"], result, suggested_field = field if field else None, suggested_doc_id = doc_id if doc_id else None)
        except Exception as e:
            print("Catturata eccezione: ", e, type (e))
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Salvataggio dei messaggi fallita nel database")
        
        return result
    
    else:
        raise Exception("Se arriva qui vuol dire che ha classificato per data un testo che non contiene alcuna indicazione temporale...")
