from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session  # noqa: F401
import os

from influxdb_client import InfluxDBClient

INFLUXDB_URL = os.environ["INFLUXDB_URL"]  # influxdb
INFLUXDB_PORT = int(os.environ["INFLUXDB_PORT"])  # 8086
INFLUXDB_TOKEN = os.environ["INFLUXDB_TOKEN"]  # homesensor:homesensor123
INFLUXDB_ORG = os.environ["INFLUXDB_ORG"]  # -
INFLUXDB_BUCKET = os.environ["INFLUXDB_BUCKET"]  # home_sensor/autogen

# sqlite:////var/lib/home-sensor/sql_app.db
SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]
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
        client = InfluxDBClient(
            url=f"http://{INFLUXDB_URL}:{INFLUXDB_PORT}", token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        )
        yield client
    finally:
        client.close()
