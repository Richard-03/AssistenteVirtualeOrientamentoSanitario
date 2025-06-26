import os
import sys

from fastapi import Request
from fastapi.templating import Jinja2Templates


ROOT_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.append(ROOT_DIR)

TEMPLATE_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "templates"
)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# API_URL="http://localhost:8000/"
API_URL="http://backend_name:8000/"
BROWSER_API_URL="http://localhost:8000/"

def recensisci_form(request: Request):
    return templates.TemplateResponse("recensisci.html", {"request": request})