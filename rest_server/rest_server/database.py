from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session  # noqa: F401
from pathlib import Path

from influxdb_client import InfluxDBClient


database_file = "sql_app.db"
database_path = Path("/var/lib/home-sensor") / database_file
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path}"
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

Base = declarative_base()


def get_db():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
    )

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_influx_db():
    try:
        token = "homesensor:homesensor123"
        client = InfluxDBClient(url="influxdb", port=8086, token=token, org="-")
        yield client
    finally:
        client.close()
