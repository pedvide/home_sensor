from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import rest_api

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc")
app.include_router(rest_api.router, prefix="/api")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
