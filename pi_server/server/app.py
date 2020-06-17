from fastapi import FastAPI

from . import rest_api
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rest_api.router, prefix="/api")


# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
# run locally uvicorn webapp.app:app --reload
# run in the pi with uvicorn webapp.app:app --reload --port 8080 --host 0.0.0.0
