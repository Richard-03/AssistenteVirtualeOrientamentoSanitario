from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os, sys
import requests

ROOT_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.append(ROOT_DIR)

TEMPLATE_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "templates"
)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# API_URL="http://localhost:8000/"
API_URL="http://backend_name:8000/"
BROWSER_API_URL="http://localhost:8000/"

def admin_login_form(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


def admin_login(request:Request,email:str=Form(...),password:str=Form(...)):
    response = requests.post(f"{API_URL}/admin/login", data={"email":email,"password":password})
    if response.status_code == 200:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Login fallito"})


def admin_dashboard(request: Request):
    try:
        response = requests.get(f"{API_URL}/admin/utenti_da_verificare")
        response.raise_for_status()
        utenti = response.json()["da_verificare"]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Errore nel caricamento dei medici")
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "utenti": utenti, "api_url": BROWSER_API_URL})


def verifica_medico(request:Request,email:str=Form(...)):
    try:
        response = requests.post(f"{API_URL}/admin/verifica_medico", data={"email":email})
        response.raise_for_status()
    except Exception:
        raise HTTPException(status_code=500, detail="Errore durante la verifica")
    return RedirectResponse(url="/admin/dashboard", status_code=302)