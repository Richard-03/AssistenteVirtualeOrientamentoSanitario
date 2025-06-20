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

OUT_OF_TASK_LIST_MSG = "Mi dispiace, in quanto assistente di un sistema sanitario posso svolgere solo compiti inerenti l'analisi dei sintomi, ricerca di medici dai nostri database e prenotazione di una visita con uno di essi."


