from database.database import get_cursor
import mariadb
from backend.llm_interaction.utilities import consume_procedure_result

def scrivi_recensione(id_appuntamento: int, id_medico: int, voto: int, commento: str):
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        cursor.callproc("aggiungi_ranking_appuntamento", (id_appuntamento, voto, commento))
        consume_procedure_result(cursor)
        print("RECENSIONE SALVATA SUL DB")
        