from server.app import app as app
from server.database import get_db, create_engine, sessionmaker, Base

from fastapi.testclient import TestClient

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
