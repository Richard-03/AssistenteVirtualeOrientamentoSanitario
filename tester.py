import requests

NEW_CHAT_TEST = 1
GET_HISTORY_TEST = 0
QA_TEST = 0
CLINICAL_SHEET_TEST = 0
INTERACTIVE_QA_TEST = 1
POS_TEST = not INTERACTIVE_QA_TEST # per modificare togliere e mettere not davanti

def get_answer(client_id, chat_id, question, history = None):
    try:
        response = requests.post("http://127.0.0.1:8000/chat/msg", json = {
            "client_id": client_id,
            "chat_id": chat_id,
            "new_msg": question,
            "history": history
        })
        response.raise_for_status()
        data = response.json()
        print(data)
    except:
        print("ERRORE post")
        raise

def new_chat(client_id):
    try:
        payload = {
            "client_id": client_id
        }
        response = requests.post("http://127.0.0.1:8000/chat", json = payload)
        response.raise_for_status()
        data = response.json()   
        print(data)
        return data
    except:
        raise Exception("ERRORE post")
    
def get_history(client_id, chat_id):
    try:
        response = requests.get("http://127.0.0.1:8000/resume_chat", params={
            "client_id": client_id,
            "chat_id": chat_id
        })
        response.raise_for_status()
        data = response.json()
        return data
    except:
        
        raise Exception("ERRORE get in get_history")

def get_clinical_sheet(client_id):
    from backend.src.backend.server import build_clinical_support_sheet
    try:
        return build_clinical_support_sheet(client_id)
    except:
        raise Exception("ERRORE: build_clinical_support_sheet non funziona correttamente")

def update_positions():
    from backend.src.database.geo import compute_coordinates
    try:
        return compute_coordinates()
    except:
        raise Exception("ERRORE: compute_coordinates non funziona correttamente")


def main():
    print("Inizio test (client_id = 1)...")
    client_id = 1  # di base None
    if client_id is None:
        client_id = int(input("Inserisci id del cliente:\n>>> "))
    chat_id = 8  # di base None
    
    if NEW_CHAT_TEST:
        print("Test new chat...")
        chat_id = new_chat(client_id)
        if chat_id:
            print(f"Ottenuta chat con id = {chat_id}")
        else:
            raise Exception("ERRORE: new_chat")

    if GET_HISTORY_TEST:
        print("Test chat esistente (client_id = 1, chat_id = 4)...")
        history = get_history(client_id, chat_id)
        print(history)

    if INTERACTIVE_QA_TEST:
        global QA_TEST
        QA_TEST = 0
        if POS_TEST:
            update_positions()
        if chat_id is None:
            chat_id = int(input("Inserire id della chat:\n>>> "))
        question = input("Inserisci problema:\n>>> ")
        get_answer(client_id, chat_id, question)
        while True:
            question = input("Continua qui:\n>>> ")
            get_answer(client_id, chat_id, question)



    if QA_TEST:
        
        if chat_id is None:
            chat_id = int(input("Inserire id della chat:\n>>> "))

        question1 = "Ho dolore alla bassa schiena, in particolare se faccio movimenti un po' forzati con gambe e glutei sento come un blocco nervoso"
        print(f"Testando: '{question1}'")
        get_answer(client_id, chat_id, question1)
    
    
        question2 = "Ho un forte prurito su tutto il corpo e sulle spalle mi sono nati moltissimi brufoli"
        print(f"Testando: '{question2}'")
        get_answer(client_id, chat_id, question2)
 
        question3 = "Sono interessato a fissare un appuntamento col dr. Luigi Verdi, quando è disponibile?"
        print(f"Testando: '{question3}'")
        get_answer(client_id, chat_id, question3)
 
        question4 = ""
        print(f"Testando: '{question4}'")
        get_answer(client_id, chat_id, question4)

        question5 = "Sai dirmi dove posso trovare un ortopedico in zona?"
        print(f"Testando: '{question5}'")
        get_answer(client_id, chat_id, question5) 

        question6 = "Che bel tempo che c'è oggi, piove!"
        print(f"Testando: '{question6}'")
        get_answer(client_id, chat_id, question6) 
 
        question7 = "Casdgf"
        print(f"Testando: '{question7}'")
        get_answer(client_id, chat_id, question7) 

       
    if CLINICAL_SHEET_TEST:
        result = get_clinical_sheet(client_id)
        print(result)


    print("Fine test...")


main()

