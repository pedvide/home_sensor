from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session  # noqa: F401
from pathlib import Path

from influxdb import InfluxDBClient


database_file = "sql_app.db"
database_path = Path(".") / database_file
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{database_path}"
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_influx_db():
    try:
        client = InfluxDBClient(
            host="influxdb", port=8086, username="homesensor", password="homesensor123"
        )
        client.switch_database("home_sensor")
        yield client
    finally:
        client.close()
