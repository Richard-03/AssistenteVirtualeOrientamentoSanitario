import mariadb

"""

This module contains just some auxiliary functions to do some data processing, not strictly related to the VirtualAssistant

"""

def estrai_nome_cognome(stringa_input):
    """Estrae il nome e il cognome da una stringa nel formato 'Nome: X, Cognome: Y'."""
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
    """Consuma il risultato di una stored procedure; per procedure con residui"""
    while True:
        try:
            if cursor.description:  # C'è un result set
                for row in cursor:
                    print("ID nuovo appuntamento:", row)
            if not cursor.nextset():
                break
        except mariadb.ProgrammingError:
            break