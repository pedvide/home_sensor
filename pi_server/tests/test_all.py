from fastapi.testclient import TestClient

from webapp.app import app

from webapp.database import clear_db, get_db
from contextlib import contextmanager

import pytest

client = TestClient(app)


@contextmanager
def fresh_db():
    try:
        yield from get_db()
    finally:
        clear_db()


@pytest.fixture
def station_zero():
    mag0 = dict(name="temp", unit="C")
    mag1 = dict(name="hum", unit="%")
    sensor0 = dict(name="am2320", magnitudes=[mag0, mag1])
    station0 = dict(token="asf3r23g2v", location="living room", sensors=[sensor0])

    sensor0_out = dict(id=0, name="am2320", magnitudes=[dict(id=0, **mag0), dict(id=1, **mag1)])
    station0_out = dict(id=0, token="asf3r23g2v", location="living room", sensors=[sensor0_out],)
    return station0, station0_out


@pytest.fixture
def station_one():
    mag0 = dict(name="temp", unit="C")
    mag1 = dict(name="hum", unit="%")
    sensor0 = dict(name="am2320", magnitudes=[mag0, mag1])
    sensor1 = dict(name="temponly", magnitudes=[mag0])
    station1 = dict(token="sfsdgsds", location="bedroom", sensors=[sensor0, sensor1])

    sensor0_out = dict(id=0, name="am2320", magnitudes=[dict(id=0, **mag0), dict(id=1, **mag1)])
    sensor1_out = dict(id=1, name="temponly", magnitudes=[dict(id=0, **mag0)])
    station1_out = dict(
        id=1, token="sfsdgsds", location="bedroom", sensors=[sensor0_out, sensor1_out],
    )
    return station1, station1_out


@pytest.fixture
def measurement_one(station_zero):

    station_in, station_out = station_zero
    sensor_out = station_out["sensors"][0]
    magnitude_out = sensor_out["magnitudes"][0]

    m0_in = dict(timestamp=1589231767, magnitude_id=0, value="25.3")
    m0_out = dict(
        id=0,
        station=station_out,
        sensor=sensor_out,
        magnitude=magnitude_out,
        timestamp=1589231767,
        value="25.3",
    )

    return m0_in, m0_out


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_one_station(station_zero):

    station_in, station_out = station_zero

    with fresh_db():
        response = client.post("/api/stations", json=station_in)
        assert response.status_code == 201
        assert response.json() == station_out

        response = client.get("/api/stations/0")
        assert response.status_code == 200
        assert response.json() == station_out

        response = client.get("/api/stations")
        assert response.status_code == 200
        assert response.json() == [station_out]


def test_get_wrong_station():

    with fresh_db():
        response = client.get("/api/stations/0")
        assert response.status_code == 404
        assert "Station not found" in response.json().values()


def test_two_stations(station_zero, station_one):

    station0_in, station0_out = station_zero
    station1_in, station1_out = station_one

    with fresh_db():
        response = client.post("/api/stations", json=station0_in)
        assert response.status_code == 201
        assert response.json() == station0_out

        response = client.post("/api/stations", json=station1_in)
        assert response.status_code == 201
        assert response.json() == station1_out

        response = client.get("/api/stations/0")
        assert response.status_code == 200
        assert response.json() == station0_out

        response = client.get("/api/stations/1")
        assert response.status_code == 200
        assert response.json() == station1_out

        response = client.get("/api/stations")
        assert response.status_code == 200
        assert response.json() == [station0_out, station1_out]


def test_post_same_station_twice(station_zero):
    station0_in, station0_out = station_zero

    with fresh_db():
        response = client.post("/api/stations", json=station0_in)
        assert response.status_code == 201
        assert response.json() == station0_out

        response = client.get("/api/stations")
        assert response.status_code == 200
        assert response.json() == [station0_out]

        # repeat POST should return first resource + 200
        response = client.post("/api/stations", json=station0_in)
        assert response.status_code == 200
        assert response.json() == station0_out

        response = client.get("/api/stations")
        assert response.status_code == 200
        assert response.json() == [station0_out]


def test_post_measurement(station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    with fresh_db():
        client.post("/api/stations", json=station_in)

        response = client.post("/api/stations/0/sensors/0/measurements", json=[m0_in])
    assert response.status_code == 201
    assert response.json() == [m0_out]


def test_get_measurement(station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    with fresh_db():
        client.post("/api/stations", json=station_in)
        client.post("/api/stations/0/sensors/0/measurements", json=[m0_in])
        response = client.get("/api/measurements")
    assert response.status_code == 200
    assert response.json() == [m0_out]


def test_get_station_measurement(station_zero, measurement_one):

    station_in, _ = station_zero
    m0_in, m0_out = measurement_one

    with fresh_db():
        client.post("/api/stations", json=station_in)
        client.post("/api/stations/0/sensors/0/measurements", json=[m0_in])
        response = client.get("/api/stations/0/measurements")
    assert response.status_code == 200
    assert response.json() == [m0_out]
