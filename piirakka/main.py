from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

app = FastAPI()

templates = Jinja2Templates(directory="piirakka/templates")
app.mount("/static", StaticFiles(directory="piirakka/static"), name="static")

@app.get("/api/hello")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request}) 

