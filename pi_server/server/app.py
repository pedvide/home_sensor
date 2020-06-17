from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import rest_api
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rest_api.router, prefix="/api")
app.mount("/", StaticFiles(directory="client/dist", html=True), name="frontend")

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
# run locally uvicorn server.app:app --reload -port 8080
# run in the pi with uvicorn server.app:app --reload --port 8080 --host 0.0.0.0
