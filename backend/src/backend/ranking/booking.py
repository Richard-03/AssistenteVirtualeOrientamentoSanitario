from backend.llm_interaction.utilities import consume_procedure_result
from backend.email.send_email import booking_mail
from database.database import get_cursor
import mariadb

def booking(client_id: int, doc_id: int, date: str):
    """Insert the appointment in the db, send conferm mail to client and doc. Doc_id should already be a verified one."""

    
    with get_cursor() as cursor:
        cursor:mariadb.Cursor

        cursor.execute("SELECT nome, cognome, email, indirizzo, telefono FROM Medico where id = ?", (doc_id, ))

        result = cursor.fetchall()[0]

        doc_name = result[0]
        doc_surname = result[1]
        doc_mail = result[2]
        address = result[3]
        phone = result[4]

        cursor.callproc("prenota_appuntamento", (client_id, doc_id, date))
        result = cursor.fetchone()
        print(f"RISULTATO DELLA FETCHONE = {result}")    
        appointment_id = result[0]
        print(f"PRESO SOLO IL PRIMO VALORE, ID APPUNTAMENTO = {appointment_id}")
        
        consume_procedure_result(cursor)
        print("PROCEDURE PER PRENOTA_APPUNTAMENTO FINITA CON SUCCESSO E RISULTATO CONSUMATO")

        # estrazione dati utili da usare nel corpo delle email
        
        cursor.execute("SELECT nome, cognome, email FROM Cliente where id = ?", (client_id, ))

        result = cursor.fetchall()[0]

        client_name = result[0]
        client_surname = result[1]
        client_mail = result[2]

        booking_mail(client_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)
        booking_mail(doc_mail, client_name, client_surname, doc_name, doc_surname, address, date, phone)
        print("EMAIL DI CONFERMA PRENOTAZIONE APPUNTAMENTO INVIATA CON SUCCESSO AD ENTRAMBE LE PARTI")