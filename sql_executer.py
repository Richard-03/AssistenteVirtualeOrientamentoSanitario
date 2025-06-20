import mariadb
from backend.src.database.database import get_cursor
import mariadb

def execute_sql(filename):
    """
    Executes all the code blocks in an sql file separated by ';'
    """
    with open(filename) as file: 
        text = file.read()
        instructions = text.split(";")
        # print(instructions)
        
        with get_cursor() as cursor:
            cursor: mariadb.Cursor
            for instruction in instructions:
                try:
                    if instruction:
                        cursor.execute(instruction)
                except:
                    print("Ultima: ", instruction)
                    raise




if input("Sure to run sql file?[y/n]").lower() == "y":
    execute_sql("temporanea/init_versione_last.sql")