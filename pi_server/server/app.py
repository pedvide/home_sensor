from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import rest_api
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rest_api.router, prefix="/api")
app.mount("/", StaticFiles(directory="client/dist", html=True), name="frontend")

origins = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
