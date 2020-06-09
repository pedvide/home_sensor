from fastapi.testclient import TestClient

from webapp.app import app as app
from webapp.database import get_db, create_engine, sessionmaker, Base

from pathlib import Path
import pytest

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
def db_session(db_engine):
    """
    Creates a new database session for a test. Note you must use this fixture
    if your test connects to db.
    """

    connection = db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def client():
    client = TestClient(app)
    return client


@pytest.fixture
def station_zero():
    mag1 = dict(name="temp", unit="C", precision=0.1)
    mag2 = dict(name="hum", unit="%", precision=0.5)
    sensor0 = dict(name="am2320", magnitudes=[mag1, mag2])
    station0 = dict(token="asf3r23g2v", location="living room", sensors=[sensor0])

    sensor0_out = dict(id=1, name="am2320", magnitudes=[dict(id=1, **mag1), dict(id=2, **mag2)])
    station0_out = dict(id=1, token="asf3r23g2v", location="living room", sensors=[sensor0_out],)
    return station0, station0_out


@pytest.fixture
def station_one():
    mag1 = dict(name="temp", unit="C", precision=0.1)
    mag2 = dict(name="hum", unit="%", precision=0.5)
    mag3 = dict(name="temp", unit="C", precision=0.05)
    sensor0 = dict(name="am2320", magnitudes=[mag1, mag2])
    sensor1 = dict(name="high_res_temp", magnitudes=[mag3])
    station1 = dict(token="sfsdgsds", location="bedroom", sensors=[sensor0, sensor1])

    sensor0_out = dict(id=1, name="am2320", magnitudes=[dict(id=1, **mag1), dict(id=2, **mag2)])
    sensor1_out = dict(id=2, name="high_res_temp", magnitudes=[dict(id=3, **mag3)])
    station1_out = dict(
        id=2, token="sfsdgsds", location="bedroom", sensors=[sensor0_out, sensor1_out],
    )
    return station1, station1_out


@pytest.fixture
def measurement_one(station_zero):
    station_in, station_out = station_zero
    sensor_out = station_out["sensors"][0]
    magnitude_out = sensor_out["magnitudes"][0]

    m0_in = dict(
        timestamp=1589231767,
        magnitude_id=magnitude_out["id"],
        sensor_id=sensor_out["id"],
        value="25.3",
    )
    m0_out = dict(
        id=1,
        station=station_out,
        sensor=sensor_out,
        magnitude=magnitude_out,
        timestamp=1589231767,
        value="25.3",
    )

    return m0_in, m0_out


@pytest.fixture
def measurement_two(station_zero):
    station_in, station_out = station_zero
    sensor_out = station_out["sensors"][0]
    magnitude_out = sensor_out["magnitudes"][0]

    m1_in = dict(
        timestamp=1589231900,
        magnitude_id=magnitude_out["id"],
        sensor_id=sensor_out["id"],
        value="20.3",
    )
    m1_out = dict(
        id=2,
        station=station_out,
        sensor=sensor_out,
        magnitude=magnitude_out,
        timestamp=1589231900,
        value="20.3",
    )

    return m1_in, m1_out


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_one_station(client, db_session, station_zero):
    station_in, station_out = station_zero

    response = client.post("/api/stations", json=station_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station_out

    response = client.get("/api/stations/1")
    assert response.status_code == 200
    assert response.json() == station_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station_out]


def test_get_wrong_station(client, db_session):
    response = client.get("/api/stations/0")
    assert response.status_code == 404
    assert "Station not found" in response.json().values()


def test_two_stations(client, db_session, station_zero, station_one):

    station0_in, station0_out = station_zero
    station1_in, station1_out = station_one

    response = client.post("/api/stations", json=station0_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station0_out

    response = client.post("/api/stations", json=station1_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "2"
    assert response.json() == station1_out

    response = client.get("/api/stations/1")
    assert response.status_code == 200
    assert response.json() == station0_out

    response = client.get("/api/stations/2")
    assert response.status_code == 200
    assert response.json() == station1_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station0_out, station1_out]

    response = client.get("/api/stations?offset=0&limit=1")
    assert response.status_code == 200
    assert response.json() == [station0_out]


def test_post_same_station_twice(client, db_session, station_zero):
    station0_in, station0_out = station_zero

    response = client.post("/api/stations", json=station0_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station0_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station0_out]

    # repeat POST should return first resource + 200
    response = client.post("/api/stations", json=station0_in)
    assert response.status_code == 200
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station0_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station0_out]


def test_modify_station(client, db_session, station_zero, station_one):
    """Create a station0, then modify it using station1's sensors"""
    station0_in, station0_out = station_zero

    station1_in, station1_out = station_one
    sensors1_in = station1_in["sensors"]
    sensors1_out = station1_out["sensors"]

    modified_station_in = dict()
    modified_station_in["token"] = station0_in["token"]
    modified_station_in["location"] = "kitchen"
    modified_station_in["sensors"] = sensors1_in
    modified_station_out = dict()
    modified_station_out["id"] = station0_out["id"]
    modified_station_out["token"] = station0_out["token"]
    modified_station_out["location"] = "kitchen"
    modified_station_out["sensors"] = sensors1_out

    # create station first
    response = client.post("/api/stations", json=station0_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station0_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station0_out]

    # PUT with new location and sensors
    response = client.put("/api/stations/1", json=modified_station_in)
    assert response.status_code == 204

    response = client.get("/api/stations/1")
    assert response.status_code == 200
    assert response.json() == modified_station_out


def test_modify_wrong_station(client, db_session, station_zero):
    station0_in, station0_out = station_zero

    # PUT a station that doesn't exist
    response = client.put("/api/stations/2", json=station0_in)
    assert response.status_code == 404


def test_sensors(client, db_session, station_zero):
    station_in, station_out = station_zero

    client.post("/api/stations", json=station_in)
    response = client.get("/api/sensors")
    assert response.status_code == 200
    # assert response.json() == [station_out]


def test_post_one_measurement(client, db_session, station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    client.post("/api/stations", json=station_in)

    response = client.post("/api/stations/1/measurements", json=[m0_in])
    assert response.status_code == 201
    assert response.json() == [m0_out]


def test_post_measurement_no_station(client, db_session):
    # POST to a station that doesn't exist
    response = client.post("/api/stations/1/measurements", json=[])
    assert response.status_code == 404


def test_post_wrong_measurement(client, db_session, station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    client.post("/api/stations", json=station_in)

    m0_in["sensor_id"] = 3
    response = client.post("/api/stations/1/measurements", json=[m0_in])
    assert response.status_code == 404
    m0_in["sensor_id"] = 1

    m0_in["magnitude_id"] = 3
    response = client.post("/api/stations/1/measurements", json=[m0_in])
    assert response.status_code == 404


def test_post_two_measurements(client, db_session, station_zero, measurement_one, measurement_two):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one
    m1_in, m1_out = measurement_two

    client.post("/api/stations", json=station_in)

    response = client.post("/api/stations/1/measurements", json=[m0_in, m1_in])
    assert response.status_code == 201
    assert response.json() == [m0_out, m1_out]


def test_get_measurement(client, db_session, station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    client.post("/api/stations", json=station_in)
    client.post("/api/stations/1/measurements", json=[m0_in])
    response = client.get("/api/measurements")
    assert response.status_code == 200
    assert response.json() == [m0_out]


def test_get_station_measurement(client, db_session, station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    client.post("/api/stations", json=station_in)
    client.post("/api/stations/1/measurements", json=[m0_in])
    response = client.get("/api/stations/1/measurements")
    assert response.status_code == 200
    assert response.json() == [m0_out]


def test_get_measurement_no_station(client, db_session):
    # POST to a station that doesn't exist
    response = client.get("/api/stations/1/measurements")
    assert response.status_code == 404
