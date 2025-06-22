import mariadb

"""

This module contains just some auxiliary functions to do some data processing, not strictly related to the VirtualAssistant

"""

def estrai_nome_cognome(stringa_input):
    """Estrae il nome e il cognome da una stringa nel formato 'Nome: X, Cognome: Y'. In caso uno non è specificato es. ritorna 'Nome: None, Cognome: Y'"""
    stringa_input = clean_string(stringa_input)
    parti = stringa_input.split(', ')

    nome = None
    cognome = None

    for parte in parti:
        if parte.startswith('Nome: '):
            nome = parte.replace('Nome: ', '')
        elif parte.startswith('Cognome: '):
            cognome = parte.replace('Cognome: ', '')
    
    return nome, cognome

def consume_procedure_result(cursor: mariadb.Cursor):
    """Consume the result of a procedure which is not to be used"""
    while True:
        try:
            if cursor.description:  # C'è un result set
                for row in cursor:
                    print("ID ritornato e scartato", row)
            if not cursor.nextset():
                break
        except mariadb.ProgrammingError:
            break

def clean_string(string: str) -> str:
    """Removes spaces and surrodings superscripts"""
    string = string.strip()

    # nella vesione usata, python 3.8.20 non ci sono removesuffix/prefix, quindi si implementano manualemnte

    while string.startswith('"') and len(string) > 0:
        string = string[1:]
    while string.endswith('"') and len(string) > 0:
        string = string[:-1]

    while string.startswith("'") and len(string) > 0:
        string = string[1:]
    while string.endswith("'") and len(string) > 0:
        string = string[:-1]

    return string