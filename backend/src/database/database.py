import mariadb
from contextlib import contextmanager
from typing import Any
 
from config import *

def _get_connection() -> mariadb.Connection:
    # nome, utente, password: tutto assegnato all'interno di init.sql
    conn = mariadb.connect(
        host = MARIA_DB_URL,
        port = MARIA_DB_PORT, 
        user = "appuser",  
        password = "userdb",  
        database = "user_db"   
    )
    return conn

@contextmanager
def get_cursor() -> Any:
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
