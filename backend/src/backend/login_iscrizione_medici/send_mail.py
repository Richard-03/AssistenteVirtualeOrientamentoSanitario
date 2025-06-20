import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendMail(mail_dest,nome,cognome):

    #mail mittente 
    mail_mittente="serviziosanitariollm@gmail.com"
    password="ipqn nzut xczw whug "

    # Crea il messaggio
    messaggio = MIMEMultipart()
    messaggio["From"] =mail_mittente
    messaggio["To"] = mail_dest
    messaggio["Subject"] = "Richiesta inviata con successo!"
    
    corpo = f"Ciao {nome} {cognome},\n\nSalve carissimo Dottore, provvederemo a fare le dovute verfiche per la registrazione del tuo account, riceverai una email di conferma quando il processo sarà terminato.\n\nCordiali saluti!"
    messaggio.attach(MIMEText(corpo, "plain"))

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


