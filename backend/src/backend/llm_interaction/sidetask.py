from fastapi import HTTPException
import requests
from datetime import datetime
from .utilities import clean_string


from config import *


class SideTaskClassifier():
    """
    This is a functional module, it contains support for the virtual assistant, but for task not related to the assistant itself.
    This is not a bot, it doesn't mantain a history. 
    """
    MODEL = OLLAMA_MODEL

    def __init__(self):
        pass

    def extract_specialization_from_direct_request(self, specialization_sentence: str) -> str:
        """From a given text in which it is specified what kind of doctor the client needs, extract the name of the specialization. Returns title case"""
        prompt = f"Nel paragrafo tra tripli apici c'è la richiesta di prenotazione da parte di un cliente per un medico,\
 in cui è specificato il tipo di medico o la specializzazione di cui ha bisogno.\
 Restituisci il nome della specializzazione corrispondende. Per esempio se la frase contiene 'neurologo' scrivi 'neurologia' oppure 'nessuna' se non c'è.\
 Il testo da analizzare è il seguente:\
 '''{specialization_sentence}'''. Scrivi solo il nome della specializzazione o 'nessuna', non aggiungere altro."
        category = self._get_response(prompt)
        return category.title()

    def classify_specialization(self, specialization_sentence) -> str:
        """From a given suggestion extract the name of the specialization in lowercase."""
        prompt = "Nel paragrafo tra tripli apici un assistente virutale per un servizio medico\
 consiglia ad un paziente di recarsi da un certo specialista. Vorrei che tu analizzassi tale messaggio\
 ed estraessi il tipo di specializzazione consigliata, ad esempio se leggi 'neurologo' tu devi rispondermi con 'neurologia'.\
 Se l'assistente è in dubbio, sta valutando diverse opzioni o non è indicato il nome di uno specialista rispondi con 'nessuna'\
 Rispondi solo con il nome della specializzazione relativa al tipo di medico consigliato o 'nessuna' se non c'è. Ecco il testo da analizzare:\
 '''" + specialization_sentence + "'''."
        category = self._get_response(prompt)
        return category.lower()
    
    def classify_booking_with_or_without_name(self, booking_sentence) -> str:
        """
        Returns the doctor if in the request. 
        Nome: <nome>, Cognome:<cognome> or 'non indicato'
        """
        prompt = "Nel paragrafo tra tripli apici un utente chiede ad un assistente virtuale per un servizio sanitario di aiutarlo a prenotare una visita presso un medico.\
 Il tuo compito è analizzare il testo e capire se vi è indicato il nome ed il cognome del medico. Se ci sono rispondi 'Nome: qui il nome della persona senza appellativo, Cognome: qui il cognome della persona senza appellativo', se manca almeno uno dei due campi o ci sono troppi medici indicati scrivi 'non indicato'.\
 Il testo è il seguente: '''" + booking_sentence + "'''. Rispondi solo con il formato 'Nome: qui il nome, Cognome: qui il cognome' o con 'non indicato'"
        category = self._get_response(prompt)
        return category


    def _get_response(self, prompt) -> str:
        """Function to get answer from with the llm"""
        payload = {
            "model": self.MODEL,
            "messages": [
                            { "role": "user", 
                            "content": prompt }
                    ],   
            "stream": False
        }
        answer: str = None
        try:
            response = requests.post(OLLAMA_URL, json = payload)
            response.raise_for_status()
            data = response.json()
            answer = data["message"]["content"]
        except HTTPException as e:
            print("ERRORE HTTP FASTAPI:", e)
            raise
        except requests.HTTPError as e:
            print("ERRORE HTTP REQUEST:", e)
            raise
        answer = clean_string(answer)
        return answer
    
    def correct_date_format(self, data_sentence) -> str:
        """Returns the correct format of a date, returning it in the form yyyy-mm-dd hh:mm:ss"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month   
        print(current_month, current_year)   
        prompt = f"Nel testo che ti fornisco tra tripli apici c'è una data di prenotazione di una visita medica.\
 Estrai informazioni sulla data.\
 Per i dati mancanti, ad esempio i secondi o i minuti, inserisci 0 o 00, se l'anno o il mese non è specificato inserisci per mese '{current_month}' e per anno '{current_year}'.\
 Ecco il testo da analizzare: '''{data_sentence}'''. Scrivi esclusivamente 'anno-mese-giorno ora:minuti:secondi' oppure 'non indicato', nessuna frase di contorno."
        result = self._get_response(prompt)
        print("Response: ", result)
        return result
