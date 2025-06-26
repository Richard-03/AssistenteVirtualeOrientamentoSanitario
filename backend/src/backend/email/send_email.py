
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import MAIL_MITTENTE, PASSWORD, NOME_SERVIZIO_SANITARIO

def send_email(mail_dest: str, subject: str, body: str):
    """Sends a generic email proviging destinatary, subject and body."""
    #mail mittente 
    mail_mittente=MAIL_MITTENTE
    password=PASSWORD

    # Crea il messaggio
    messaggio = MIMEMultipart()
    messaggio["From"] = mail_mittente
    messaggio["To"] = mail_dest
    messaggio["Subject"] = subject
    
    messaggio.attach(MIMEText(body, "plain"))

    try:
        # Connessione al server SMTP di Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(mail_mittente, password)
        server.sendmail(mail_mittente, mail_dest, messaggio.as_string())
        server.quit()
        print("Email inviata con successo!")
    except Exception as e:
        print("Errore durante l'invio dell'email:", e)

def send_doc_wait_for_verify(mail_dest:str, nome:str, cognome:str):
    subject = "Richiesta inviata con successo!"
    body = f"Ciao {nome} {cognome},\n\nSalve carissimo Dottore, provvederemo a fare le dovute verfiche per la registrazione del tuo account, riceverai una email di conferma quando il processo sarà terminato.\n\nCordiali saluti!"
    send_email(mail_dest, subject, body)

def send_mail_for_user_subscription(mail_dest,nome,cognome):
    subject = "Registrazione avvenuta con successo!"
    body = f"Ciao {nome} {cognome},\n\nBenvenuto nel nostro servizio!"
    send_email(mail_dest, subject, body)

def booking_mail(mail_dest: str, nome:str, cognome:str, nome_doc: str, cognome_doc: str, indirizzo: str, date: str, telefono: int = None):
    subject = f"Prenotazione avvenuta con successo presso {NOME_SERVIZIO_SANITARIO}!"
    body = f"Prenotazione confermata!\n\nDi seguito riportiamo i dettagli della prenotazione avvenuta con successo:\n\n- Cliente: {nome} {cognome}\n- Dr./Dr.essa: {nome_doc} {cognome_doc}\n- Data: {date}\n- Presso: {indirizzo}" + f"\n- Telefono: {telefono}" if telefono else "" + f"\n\n\Buon proseguimento, \nLo staff di {NOME_SERVIZIO_SANITARIO}"
    send_email(mail_dest, subject, body)

def send_appointment_cancellation(mail_dest: str, appointment_date: str):
    subject = f"Annullamento prenotazione in data {appointment_date}!"
    body = f"Ci scusiamo, il vostro appuntamento in data {appointment_date} è stato annullato"
    send_email(mail_dest, subject, body)
