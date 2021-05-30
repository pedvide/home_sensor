from rest_server.app import app as app
from rest_server.database import (
    get_db,
    get_influx_db,
    create_engine,
    sessionmaker,
    Base,
    InfluxDBClient,
)

from fastapi.testclient import TestClient

from pathlib import Path
import shutil
import pytest
import requests
import datetime

from xprocess import ProcessStarter


@pytest.fixture(scope="session")
def influxdb_server(xprocess):
    class Starter(ProcessStarter):
        pattern = "Listening for signals"
        args = ["influxd", "run", "-config", "/etc/influxdb/influxdb.conf"]

    influxdb_data = "/tmp/influxdb/"
    if Path(influxdb_data).exists():
        shutil.rmtree(influxdb_data, ignore_errors=True)
    xprocess.ensure("influxd", Starter)
    response = requests.post(
        "http://localhost:8086/query", data={"q": "CREATE DATABASE home_sensor"}
    )
    response.raise_for_status()
    yield
    xprocess.getinfo("influxd").terminate()
    if Path(influxdb_data).exists():
        shutil.rmtree(influxdb_data, ignore_errors=True)


database_file = "test_sql_app.db"
database_path = Path(".") / database_file
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{database_file}"


@pytest.fixture(scope="session")
def db_engine():
    """Session-wide test database."""
    if database_path.exists():
        database_path.unlink()

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
    )
    Base.metadata.create_all(bind=engine)

    yield engine

    if database_path.exists():
        database_path.unlink()


@pytest.fixture(scope="function")
def db_session(db_engine, influxdb_server):
    """
    Creates a new database session for a test. Note you must use this fixture
    if your test connects to db.
    """

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    def override_get_influx_db():
        try:
            client = InfluxDBClient(url="127.0.0.1:8086", token=":", org="-")
            response = requests.post(
                "http://localhost:8086/query", data={"q": "CREATE DATABASE home_sensor"}
            )
            response.raise_for_status()
            yield client
        finally:
            client.close()

    try:
        connection = db_engine.connect()
        transaction = connection.begin()
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
        session = TestingSessionLocal()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_influx_db] = override_get_influx_db

        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

        with InfluxDBClient(url="127.0.0.1:8086", token=":", org="-") as _:
            response = requests.post(
                "http://localhost:8086/query", data={"q": "DROP DATABASE home_sensor"}
            )
            response.raise_for_status()


@pytest.fixture(scope="session")
def client():
    client = TestClient(app)
    return client


@pytest.fixture
def sensor_one():
    mag1 = dict(name="temp", unit="C", precision=0.1)
    mag2 = dict(name="hum", unit="%", precision=0.5)
    sensor1 = dict(name="am2320", magnitudes=[mag1, mag2])
    sensor1_out = dict(
        id=1, name="am2320", magnitudes=[dict(id=1, **mag1), dict(id=2, **mag2)], tag=None
    )
    return sensor1, sensor1_out


@pytest.fixture
def sensor_two():
    mag3 = dict(name="temp", unit="C", precision=0.05)
    sensor2 = dict(name="high_res_temp", magnitudes=[mag3], tag="1")
    sensor2_out = dict(id=2, name="high_res_temp", magnitudes=[dict(id=3, **mag3)], tag="1")
    return sensor2, sensor2_out


@pytest.fixture
def station_one():
    station1 = dict(token="asf3r23g2v", location="living room", hostname="esp-1.home")
    station1_out = dict(
        id=1, token="asf3r23g2v", location="living room", hostname="esp-1.home", sensors=[]
    )
    return station1, station1_out


@pytest.fixture
def station_two():
    station2 = dict(token="sfsdgsds", location="bedroom", hostname="esp-2.home")
    station2_out = dict(
        id=2, token="sfsdgsds", location="bedroom", hostname="esp-2.home", sensors=[]
    )
    return station2, station2_out


@pytest.fixture
def measurement_one(station_one, sensor_one):
    station_in, station_out = station_one
    sensor_in, sensor_out = sensor_one
    magnitude_out = sensor_out["magnitudes"][0]

    now = int(datetime.datetime.now().timestamp())

    m1_in = dict(
        timestamp=now,
        magnitude_id=magnitude_out["id"],
        sensor_id=sensor_out["id"],
        value="25.3",
    )
    m1_out = dict(
        # id=1,
        station_id=station_out["id"],
        sensor_id=sensor_out["id"],
        magnitude=magnitude_out,
        timestamp=now,
        value="25.3",
    )

    return m1_in, m1_out


@pytest.fixture
def measurement_two(station_one, sensor_one):
    station_in, station_out = station_one
    sensor_in, sensor_out = sensor_one
    magnitude_out = sensor_out["magnitudes"][0]

    now = int(datetime.datetime.now().timestamp())

    m2_in = dict(
        timestamp=now,
        magnitude_id=magnitude_out["id"],
        sensor_id=sensor_out["id"],
        value="20.3",
    )
    m2_out = dict(
        # id=2,
        station_id=station_out["id"],
        sensor_id=sensor_out["id"],
        magnitude=magnitude_out,
        timestamp=now,
        value="20.3",
    )

    return m2_in, m2_out
