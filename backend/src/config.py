"""
This module is thought to be a file to tune easily some parameters.
"""


DOCKER = True

if DOCKER:
    OLLAMA_URL = "http://ollama_service:11434/api/chat"
else:
    OLLAMA_URL = "http://localhost:11434/api/chat"


OLLAMA_MODEL = "gemma3:4b" # "llama3:8b"

ANSWER_LENGTH_LIMIT = 300

MARIA_DB_PORT = 3307 if not DOCKER else 3306
MARIA_DB_URL = "127.0.0.1" if not DOCKER else "mariadb"

NOME_SERVIZIO_SANITARIO = "Servizio Sanitario LLM"
MAIL_MITTENTE="serviziosanitariollm@gmail.com"
PASSWORD ="ipqn nzut xczw whug "

FRONTEND_PORT = "8001"
FRONTEND_NAME = "localhost:" + FRONTEND_PORT
BACKEND_NAME = "backend_name"
REDIS_NAME = "redis"

COUNTDOWN_REVIEW_EMAIL = 30 # secondi di countdown dalla prenotazione di un appuntamento

SYSTEM_ROBUST_OUTPUT = "Messaggio di sistema: si è verificato un errore nella comunicazione con l'assistente AI, probabilmente dovuto a misclassificazione del modello, si prega di riprovare, tornando alla selezione chat o scrivendo direttamente nuovi messaggi. Si ricorda che questo assistente è progettato per rispondere a richieste classificabili come: \n - Descrizione dei sintomi\n - Richiesta specialisti, fornendo il nome della specializzazione \n - Aiuto in pratiche di prenotazione, fornendo indicazioni su nome e cognome del medico e solo dopo che le sono fatte vedere le disponibilità potrà indicare una data. " 

AVAILABILITY_TIME_WINDOW = 3    # numero di giorni da prendere in considerazione