import smtplib
import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# TODO: utilizzare un file .env o comunque un file config per caricare email e password
NOME_SERVIZIO_SANITARIO = "Servizio Sanitario LLM"
MAIL_MITTENTE="serviziosanitariollm@gmail.com"
PASSWORD ="ipqn nzut xczw whug "

def sendMail(mail_dest,nome,cognome):

    # Crea il messaggio
    messaggio = MIMEMultipart()
    messaggio["From"] = MAIL_MITTENTE
    messaggio["To"] = mail_dest
    messaggio["Subject"] = "Registrazione avvenuta con successo!"
    
    corpo = f"Ciao {nome} {cognome},\n\nBenvenuto nel nostro servizio!"
    messaggio.attach(MIMEText(corpo, "plain"))

    try:
        # Connessione al server SMTP di Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_MITTENTE, PASSWORD)
        server.sendmail(MAIL_MITTENTE, mail_dest, messaggio.as_string())
        server.quit()
        print("Email inviata con successo!")
    except Exception as e:
        print("Errore durante l'invio dell'email:", e)


def booking_mail(mail_dest: str, nome:str, cognome:str, nome_doc: str, cognome_doc: str, indirizzo: str, date: str, telefono: int = None):
    
    messaggio = MIMEMultipart()
    messaggio["From"] = MAIL_MITTENTE
    messaggio["To"] = mail_dest
    messaggio["Subject"] = f"Prenotazione avvenuta con successo presso {NOME_SERVIZIO_SANITARIO}!"

    corpo = f"Prenotazione confermata!\n\nDi seguito riportiamo i dettagli della prenotazione avvenuta con successo:\n\n- Cliente: {nome} {cognome}\n- Dr./Dr.essa: {nome_doc} {cognome_doc}\n- Data: {date}\n- Presso: {indirizzo}" + f"\n- Telefono: {telefono}" if telefono else "" + f"\n\n\Buon proseguimento, \nLo staff di {NOME_SERVIZIO_SANITARIO}"
    messaggio.attach(MIMEText(corpo, "plain"))

    try:
        # Connessione al server SMTP di Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_MITTENTE, PASSWORD)
        server.sendmail(MAIL_MITTENTE, mail_dest, messaggio.as_string())
        server.quit()
        print("Email inviata con successo!")
    except Exception as e:
        print("Errore durante l'invio dell'email:", e)

