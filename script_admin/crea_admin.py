import sys
import mariadb
import bcrypt
import time

# TODO: definire un file di configurazione da cui gesitre le variabili di setup

DOCKER = True
MARIA_DB_PORT = 3307 if not DOCKER else 3306
MARIA_DB_URL = "127.0.0.1" if not DOCKER else "mariadb"

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









def connect(max_retries=30, retry_delay=2):
    """Connect to MariaDB with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            conn = _get_connection()
            print("Successfully connected to database!")
            return conn
        except mariadb.Error as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All connection attempts failed!")
                sys.exit(1)

def test_database_access(conn):
    """Test basic database operations"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 as test")
        result = cur.fetchone()
        cur.close()
        print(f"Database test successful: {result}")
        return True
    except mariadb.Error as e:
        print(f"Database test failed: {e}")
        return False

def inserisci_admin(conn, email, password):
    try:
        cur = conn.cursor()
        
        # Genera hash bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')        
        # Elimina se già esiste
        cur.execute("DELETE FROM Admin WHERE email = ?", (email,))
        # Inserisci admin nuovo
        cur.execute("INSERT INTO Admin (email, password) VALUES (?, ?)", (email, hashed))

        cur.close()
        conn.commit()
        print("✅ Admin inserito con successo.")

    except mariadb.Error as e:
        print(f"Errore admin")
        conn.rollback()


if __name__ == "__main__":
    print("Starting admin population script...")
    
    # Connect to database
    conn = connect()
    
    # Test database access
    if not test_database_access(conn):
        print("Database access test failed. Exiting.")
        sys.exit(1)
    

    # Dati dell'admin
    email = "admin@example.com"
    password = "admin123"

    # Process clients
    try:
        print("\nProcessing admins...")
        
        # TODO: se si vuole popolare con più di 1 admin, inserire qui un ciclo for e trasformare email e password in un dizionario
        inserisci_admin(conn, email, password)
    except Exception as e:
        print(f"Error processing admin: {e}")
    