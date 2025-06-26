
# Endpoint per eliminare un appuntamento (aggiorna lo stato a 'Eliminato')
from fastapi import Form, HTTPException
from backend.doctor.login_iscrizione import execute_query, format_value
from database.database import _get_connection, get_cursor
import mariadb
from backend.llm_interaction.utilities import consume_procedure_result

from backend.email.send_email import send_appointment_cancellation

def elimina_appuntamento(id_appuntamento: int):
    conn = _get_connection()
    # TODO: USARE LA STORED PROCEDURE APPOSITA
    query = f"""
    UPDATE Agenda
    SET stato = 'Eliminato'
    WHERE id = {id_appuntamento} 
    """

    try:
        #execute_query(conn, query)
 
        # SOSTITUZIONE con stored procedeure
        with get_cursor() as cursor:
            cursor: mariadb.Cursor

            # prendo le informazini per notificare le parti dell'eliminazione dell'appuntamento
            cursor.execute("SELECT Medico.email, Cliente.email, Appuntamento.data_appuntamento FROM Appuntamento join Medico on Appuntamento.id_medico = Medico.id join Cliente on Appuntamento.id_cliente = Cliente.id WHERE Appuntamento.id = ?", (id_appuntamento, ))
            medico_mail, cliente_mail, data_appuntamento = cursor.fetchall()[0]
            
            cursor.callproc("elimina_appuntamento_logico", (id_appuntamento, ))
            consume_procedure_result(cursor)

            # invio successivo all'eliminazione in modo da non avere problemi di coerenza in caso di operazioni fallite
            send_appointment_cancellation(medico_mail, data_appuntamento)
            send_appointment_cancellation(cliente_mail, data_appuntamento)
            print("EMAIL DI CANCELLAZIONE INVIATE LATO MEDICO")

        return {"message": "Appuntamento eliminato con successo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'eliminazione: {str(e)}")


def aggiorna_disponibilita(
    id_medico: int = Form(...),
    disponibilita: str = Form(...)
):
    import json
    from datetime import datetime

    try:
        disponibilita_list = json.loads(disponibilita)
        if not isinstance(disponibilita_list, list) or not disponibilita_list:
            raise ValueError("Formato lista non valido.")
        for dt in disponibilita_list:
            datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Disponibilità non valida: {str(e)}")

    conn = _get_connection()

    try:
        # elimina appuntamenti futuri
        delete_query = f"""
        DELETE FROM Agenda 
        WHERE id_medico = {format_value(id_medico)} 
        AND stato = 'Disponibile';
        """
        execute_query(conn, delete_query)

        # reinserisci nuovi slot
        for fascia in disponibilita_list:
            query_slot = f"CALL insert_appuntamento({id_medico}, {format_value(fascia)});"
            execute_query(conn, query_slot)

        return {"message": "Disponibilità aggiornata con successo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore aggiornamento: {str(e)}")