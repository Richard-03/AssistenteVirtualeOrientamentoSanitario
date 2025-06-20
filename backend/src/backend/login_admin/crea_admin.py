import mariadb
import bcrypt

# TODO: definire un file di configurazione da cui gesitre le variabili di setup

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




# Dati di connessione al database
conn = _get_connection()
cursor = conn.cursor()

# Dati dell'admin
email = "admin@example.com"
password = "admin123"

# Genera hash bcrypt
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Elimina se già esiste
cursor.execute("DELETE FROM Admin WHERE email = ?", (email,))

# Inserisci admin nuovo
cursor.execute("INSERT INTO Admin (email, password) VALUES (?, ?)", (email, hashed))
conn.commit()

cursor.close()
conn.close()
print("✅ Admin inserito con successo.")