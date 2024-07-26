from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from typing import Annotated
import models
from database import engine, get_db
from sqlalchemy.orm import Session
import auth.auth as auth
from auth.auth import get_current_user
from routers import projects, skills, users, requests
import logging
import logging.handlers
from starlette.middleware.base import BaseHTTPMiddleware

models.Base.metadata.create_all(bind=engine)

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", mode='a'),  # Write logs to a file named 'app.log'
        logging.StreamHandler()  # Keep the console output
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
logger.info("Starting API....")

#Create a log of the http requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/1.1\"")
        response = await call_next(request)
        logger.info(f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/1.1\" {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(skills.router)
app.include_router(requests.router)

templates = Jinja2Templates(directory="..\\frontend\\templates")



db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/")
async def homepage(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("login.html", context)

@app.get("/notfound")
async def notfound(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("404.html", context)
