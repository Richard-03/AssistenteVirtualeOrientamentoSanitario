from celery import Celery
from config import NOME_SERVIZIO_SANITARIO, MAIL_MITTENTE, PASSWORD, FRONTEND_NAME, REDIS_NAME
from backend.email.send_email import send_email

celery = Celery("tasks", broker=f"redis://{REDIS_NAME}:6379", backend=f"redis://{REDIS_NAME}:6379")

@celery.task
def richiesta_recensione_ritardata(client_email, id_appuntamento, id_medico):
    link = f"http://{FRONTEND_NAME}/recensisci?id_app={id_appuntamento}&id_medico={id_medico}"
    corpo = f"Lascia una recensione per migliorare il sistema interno di {NOME_SERVIZIO_SANITARIO}!\n\n\n Raccontaci com' è andata!\n\n Clicca sul link per recensire il tuo appuntamento: {link}"

    send_email(client_email, subject="La tua opinione conta", body=corpo)

