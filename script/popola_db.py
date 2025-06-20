import csv
import mariadb
import time
import sys

def connect(max_retries=30, retry_delay=2):
    """Connect to MariaDB with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            conn = mariadb.connect(
                host="mariadb",
                port=3306,
                user="appuser",
                password="userdb",
                database="user_db",
                connect_timeout=10
            )
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

def inserisci_cliente(conn, row):
    try:
        cur = conn.cursor()
        cur.callproc('insert_cliente_completo', (
            row['nome'], row['cognome'], row['indirizzo'], row['citta'],
            row['email'], row['password'], int(row['eta']), row['sesso'],
            float(row['peso']), float(row['altezza']),
            row.get('intolleranze', ''), row.get('condizioni_pregresse', ''),
            row.get('condizioni_familiari', ''), None
        ))
        # Controllo se stored_results è disponibile
        if hasattr(cur, 'stored_results'):
            for res in cur.stored_results():
                print("Cliente:", res.fetchall())
        cur.close()
        conn.commit()
    except mariadb.Error as e:
        print(f"Errore cliente {row.get('email')}: {e}")
        conn.rollback()

def inserisci_medico(conn, row):
    try:
        cur = conn.cursor()

        # TODO: MODIFICA QUI PER IL CALCOLO DELLE COORDINATE DA PASSARE DIRETTAMENTE ALLA STORED PROCEDURE (I DATI SONO FINTI ORA)
        
        cur.callproc('insert_medico_completo_csv', (
            row.get('nome'), row.get('cognome'), row.get("codice_fiscale"), 
            row.get("numero_albo"), row.get("citta_ordine"), 
            row.get("data_iscrizione_albo"), row.get("citta"), row.get('email'),
            row.get("password"), row.get('telefono', ''),
            row.get('url_sito', ''), row.get('indirizzo', ''),
            row.get('specializzazioni'), row.get('coordinate')
        ))
        if hasattr(cur, 'stored_results'):
            for res in cur.stored_results():
                print("Medico:", res.fetchall())
        cur.close()
        conn.commit()
    except mariadb.Error as e:
        print(f"Errore medico {row.get('email')}: {e}")
        conn.rollback()

# Main execution
if __name__ == "__main__":
    print("Starting database population script...")
    
    # Connect to database
    conn = connect()
    
    # Test database access
    if not test_database_access(conn):
        print("Database access test failed. Exiting.")
        sys.exit(1)
    
    # Process clients
    try:
        print("\nProcessing clients...")
        with open('clienti_csv.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader, 1):
                print(f"Processing client {i}: {row['nome']} {row['cognome']}")
                inserisci_cliente(conn, row)
    except FileNotFoundError:
        print("clienti_csv.csv file not found!")
    except Exception as e:
        print(f"Error processing clients: {e}")
    
    # Process doctors
    try:
        print("\nProcessing doctors...")
        with open('medici_csv.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader, 1):
                print(f"Processing doctor {i}: {row['nome']} {row['cognome']}")
                inserisci_medico(conn, row)
    except FileNotFoundError:
        print("medici_csv.csv file not found!")
    except Exception as e:
        print(f"Error processing doctors: {e}")
    
    # Close connection
    conn.close()
    print("\nDatabase population completed!")
