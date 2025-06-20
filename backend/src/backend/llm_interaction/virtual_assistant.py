from config import *
from typing import List, Dict, Any
from fastapi import HTTPException
import requests


#################################################################################################################
#                                                                                                               #
# ALL PROMPT ARE IN THE FORM 'INSTRUCTIONS +  ''' + USER PROMPT + ''' + INSTRUCTIONS" AND MUST BE IN THIS FORM  #
#                                                                                                               #
#################################################################################################################

VEDI_STORIA_INTEGRALE = False


class VirtualMedicalAssistant:

    """This class represent the actual Assintant, all the functions of this class are relative to the task the MedicalAssitant has to deal with"""

    MODEL = OLLAMA_MODEL



    DESCRIPTION_TASK = "comprensione del problema di salute"
    
    SEARCH_WITHOUT_DESCRIPTION = "ricerca specialisti senza descrizione"
    SEARCH_TASK = "ricerca specialisti con descrizione"
    
    BOOKING_TASK_NO_DATE = "prenotazione visita senza data"
    BOOKING_TASK_WITH_DATE = "prenotazione visita a data fissata"
    TASK_LIST = [DESCRIPTION_TASK, SEARCH_TASK, SEARCH_WITHOUT_DESCRIPTION, BOOKING_TASK_NO_DATE, BOOKING_TASK_WITH_DATE]
    
    def __init__(self, history = None):
        """Creates the object and initialize the agent giving it explaination about what it can and cannot do"""
        self._history: List[Dict[str, str]] = history if history else []
        # initializing context if there is no one
        if not self._history:
            response = self._get_response_by_prompt(
f"D'ora in poi sei l'assistente virtuale per un servizio sanitario;\
 dovrai aiutare i clienti sia con i sintomi che manifestano, sia con le procedure di prenotazione di visite mediche. \
 Il tipico flusso di lavoro che intraprenderai sarà fatto in questo modo: \
 il paziente ti dirà come si sente, che problema ha, ne analizzerai i sintomi e consiglierai specialisti adeguati,\
 poi potresti dovergli mostrare se nelle vicinanze ci sono medici di quel tipo ed infine potresti fissare una visita.\
 Il flusso di lavoro tipico è questo ma dovrai saper essere flessibile sull'ordine dei task che ti vengono commisionati.\
 Se una richiesta o un testo in input non è inerente a questo contesto invia un messaggio che faccia intendere all'utente quali sono le tue mansioni.\
 Se non ti è immediatamente chiaro che specialista consigliare, devi fare più domande, il tuo \
 obiettivo primario è la precisione, devi cercare di inviare il cliente dallo specialista più adatto possibile e consigliare \
 eventuali controlli o analisi o esami da fare in modo da arrivare preparato alla visita.\
 Inoltre le tue risposte non dovranno mai essere più lunghe di {ANSWER_LENGTH_LIMIT} parole. Chiaro? Rispondi solo sì/no"
            )
            print("Assistente virtuale pronto...")

    def get_history(self) -> List[Dict[str, str]]:
        """Return history of the user-ollama model interaction"""
        return self._history

    def _add_to_history(self, prompt: str, role: str) -> None:
        """Adds a message in the history in the specifyied role"""
        self._history.append({
            "role": role,
            "content": prompt
        })

    def _get_response_by_prompt(self, prompt: str) -> str:
        """
        Adds the complete prompt to the history of the assistant,
        send it to the ollama model,
        finally save the answer in the history of the assistant. 
        Args:
            prompt (str):
        Raises:
            Exception: error connecting with ollama service
        Returns:
            str: answer
        """
        self._add_to_history(prompt, role = "user")
        payload = {
            "model": self.MODEL,
            "messages": self._history,
            "stream": False
        }
        answer: str = None
        try:
            response = requests.post(OLLAMA_URL, json = payload)
            response.raise_for_status()
            data = response.json()
            answer = data["message"]["content"]
        except HTTPException as e:
            print("Errore HTTP FASTAPI in _get_reponse_by_prompt:", e)
            raise
        except requests.HTTPError as e:
            print("Errore HTTP REQUEST in _get_reponse_by_prompt:", e)
            raise

        if answer:
            self._add_to_history(answer, role = "assistant")
            if VEDI_STORIA_INTEGRALE: 
                print("Storia della chat integrale: \n\n\n")
                print(self._history)
                print("\n\n\n")
            return answer
        
        # il seguente codice non dovrebbe mai essere eseguito, è instrumentazione per bug imprevisto
        self._history.pop()
        print("Eseguendo riga che non andrebbe eseguita")
        raise Exception("ERRORE in _get_response_by_prompt: nonostante non ci siano errori http, answer è vuoto")

    def classify_task(self, task: str) -> str:
        """Classify the task the assitant has to answer based on the reqeust. This will not be part of the history."""
        prompt = f"Basandoti sulla storia della conversazione, classifica la frase tra tripli apici\
 in una delle seguenti categorie, in modo da individuare la fase della conversazione:\
 '{self.DESCRIPTION_TASK}' se la frase riguarda la descrizione di sintomi, malesseri, stati fisici o emotivi percepiti dal cliente,\
 '{self.SEARCH_TASK}' se il cliente sa già a quale specialista rivolgersi e vuole sapere se puoi aiutarlo a trovare specialisti in zona,\
 '{self.BOOKING_TASK_NO_DATE}' se il cliente ha già il nome di uno specialista specifico e vorrebbe che lo aiutassi nelle pratiche di prenotazione,\
 '{self.BOOKING_TASK_WITH_DATE}' se il cliente sta indicando una data relativa al dottore precedentemente specificato,\
 '{self.SEARCH_WITHOUT_DESCRIPTION} se il cliente sta chiedendo informazioni su un tipo di specialista senza aver prima parlato dei suoi sintomi durante la conversazione'.\
 Se una richiesta o un testo in input non è inerente al contesto medico o alla conversazione in corso allora scrivi 'senza categoria'. ''' {task} '''.\
 Rispondi solo con il nome della categoria o con 'senza categoria'.\
 Usa la storia della conversazione per risolvere le ambiguità."
        
        category = self._get_response_by_prompt(prompt)

        # cleanup: removing classification message, they are not part of the chat
        self._history.pop()
        self._history.pop()

        return category
    
    def analyze_symptoms(self, description: str, support_clinical_infos: str) -> str:
        """Based on a description and a clinical history if any, analyses symptoms and return the name of the specialization."""
        # TODO: vedendo i risultati questo prompt va migliorato, come?
        # ad esempio non sempre restituisce il formato che gli dico, ad esemipo [ostetricia/ginecologia] invece di [ostetricia, ginecologia] -> potrebbe essere un problema del modello o al fromato dei dati
        
        print("Dati formattati in ingresso all'analisi dei sintomi:", support_clinical_infos)

        response = self._get_response_by_prompt(
f"Di seguito, il testo contenuto tra gli apici tripli contiene una richiesta di aiuto da parte del cliente:\
 '''{description}'''. Sulla base di tale richiesta interagisci con l'utente al fine di indirizzarlo\
 allo specialista più idoneo e di prepararlo a un'eventuale visita." + f" Del cliente sai anche le seguenti informazioni,\
 che puoi usare al fine di fornire una risposta più precisa e personalizzata: ''{support_clinical_infos}.''" if support_clinical_infos else "" +
 " Rispondi in modo professionale e sintetico. Puoi anche consigliare qualcosa da fare nel periodo antecedente la visita."
        )
        
        return response


    def handle_search(self, request: str, data: List) -> str:
        """Based on doc data passed, elaborates an answer listing the best doctors basing on ranking and position."""
        # TODO: arricchirre questa e tutte le funzioni a ritroso delle informazioni circa il ranking; 
        # TODO: capire se l'imprecisione è dovuta al formato dei dati che arrivano 
        
        print("ATTENZIONE: IL SISTEMA DI RANKING NON è CORRENTEMENTE IMPLEMENTATO")
        print("Dati per handle_search: ", data)

        if data:
            response = self._get_response_by_prompt(
f"Arriva la richiesta di ricerca di specialisti nelle vicinanze da parte dell'utente come segue:\
 '''{request}'''. Rispondi usando le seguenti informazioni: ''{data}''.\
 Elenca i medici nel formato 'nome cognome (specializzazione | indirizzo, distanza)'.\
 Suggerisci inoltre di controllare la mappa generata per avere una visione grafica delle informazioni.\
 Infine chedi se desidera prenotare una visita con uno dei medici mostrati, indicando eventualmente quale.\
 Se non ricevi dati comunica che non abbiamo specialisti registrati che rispondono alla richiesta."
        )
        else: 
            response = f"Arriva la richiesta di ricerca di specialisti nelle vicinanze da parte dell'utente come segue:\
 '''{request}'''. Rispondi dicendo che al momento non abbiamo medici registrati che soddisfano la richiesta."
        return response
    
    def ask_for_booking_without_name(self, request:str, doc_list: List[Dict[str, Any]]) -> str:
        """Handle booking request without the name of a doctor."""

        # TODO: analisi della risposta in base ai dati come arrivano
        print("Dati per prenotazione senza nome: ", doc_list)

        prompt = f"Arriva la richiesta di un cliente che vorrebbe prenotare con un medico. La richiesta è la seguente: '''{request}'''. Rispondi usando le seguenti informazioni: {doc_list}. Elenca 'nome cognome (specializzazione | indirizzo, distanza)' per ciascuno. "
        result = self._get_response_by_prompt(prompt)
        return result

    def ask_for_booking_date(self, request: str, doc_data: Dict[str, Any]) -> str:
        """Handle booking request containing the name of a doctor."""

        # TODO: analisi della risposta in base ai dati come arrivano
        print("Dati per prenotazione con nome: ", doc_data)

        clean_doc_data = {key:value for key,value in doc_data.items() if key in ["nome", "cognome", "indirizzo", "distanza_km", "specializzazione"]}
        prompt = f"Arriva la richiesta di prenotazione per un medico, come segue tra tripli apici:'''{request}''''. \
 Chiedi all'utente data e ora della prenotazione per una visita con lo specialista indicato nei seguenti dati: {clean_doc_data}. \
 Se nella richiesta l'utente aveva già proposto una data chiedi di riscriverla."
        result = self._get_response_by_prompt(prompt)
        return result
    

    # la seguente non è mai usata per ora
    def ask_to_repeat(self):
        result = self._get_response_by_prompt("Chidi di ripetere perché non hai capito bene")
        return result