"""Test sensor and measurement related endpoints"""

import pytest


@pytest.fixture
def setup_station_one(client, db_session, station_one, sensor_one):
    station_in, station_out = station_one
    sensor_in, sensor_out = sensor_one
    station_in["sensors"] = [sensor_in]
    station_out["sensors"] = [sensor_out]

    client.post("/api/stations", json=station_in)

    return station_out, sensor_out


def test_sensors(client, db_session, setup_station_one):
    station_out, sensor_out = setup_station_one

    response = client.get("/api/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor_out]


def test_post_one_measurement(client, db_session, setup_station_one, measurement_one):
    m1_in, m1_out = measurement_one

    response = client.post("/api/stations/1/measurements", json=[m1_in])
    assert response.status_code == 201
    assert response.json() == [m1_out]


def test_post_measurement_no_station(client, db_session):
    # POST to a station that doesn't exist
    response = client.post("/api/stations/1/measurements", json=[])
    assert response.status_code == 404


def test_post_wrong_measurement(client, db_session, setup_station_one, measurement_one):
    m1_in, m1_out = measurement_one

    m1_in["sensor_id"] = 3
    response = client.post("/api/stations/1/measurements", json=[m1_in])
    assert response.status_code == 404
    m1_in["sensor_id"] = 1

    m1_in["magnitude_id"] = 3
    response = client.post("/api/stations/1/measurements", json=[m1_in])
    assert response.status_code == 404


def test_post_two_measurements(
    client, db_session, setup_station_one, measurement_one, measurement_two
):
    m1_in, m1_out = measurement_one
    m2_in, m2_out = measurement_two

    response = client.post("/api/stations/1/measurements", json=[m1_in, m2_in])
    assert response.status_code == 201
    assert response.json() == [m1_out, m2_out]


def test_get_measurement(client, db_session, setup_station_one, measurement_one):
    m1_in, m1_out = measurement_one

    client.post("/api/stations/1/measurements", json=[m1_in])
    response = client.get("/api/measurements")
    assert response.status_code == 200
    assert response.json() == [m1_out]


def test_get_station_measurement(client, db_session, setup_station_one, measurement_one):
    m1_in, m1_out = measurement_one

    client.post("/api/stations/1/measurements", json=[m1_in])
    response = client.get("/api/stations/1/measurements")
    assert response.status_code == 200
    assert response.json() == [m1_out]


def test_get_measurement_no_station(client, db_session):
    # POST to a station that doesn't exist
    response = client.get("/api/stations/1/measurements")
    assert response.status_code == 404
