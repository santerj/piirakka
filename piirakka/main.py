import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import model

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
import model.sidebar_item


app = FastAPI()

templates = Jinja2Templates(directory="piirakka/templates")
app.mount("/static", StaticFiles(directory="piirakka/static"), name="static")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html",
                {
                    "request": request,
                    "sidebar_items": model.sidebar_item.sidebar_items
                }
    ) 
