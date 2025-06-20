import mariadb
from contextlib import contextmanager
from typing import Any
 
from config import *


# TODO: modifiare in login_back_utenti e adattare e snellire con il context manager qui sotto
# usare lì, e ovunque serve connettersi al database solo get_cursor

def _get_connection() -> mariadb.Connection:
    # nome, utente, password: tutto assegnato all'interno di init.sql
    conn = mariadb.connect(
        host = MARIA_DB_URL,
        port = MARIA_DB_PORT, 
        user = "appuser",  
        password = "userdb",  
        database = "user_db"   
    )

    """     
    user = "root",  
    password = "rootpassword",  
    database = "user_db"    
    """

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
