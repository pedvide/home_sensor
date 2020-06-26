"""Test sensor and measurement related endpoints"""


def test_sensors(client, db_session, station_zero):
    station_in, station_out = station_zero

    client.post("/api/stations", json=station_in)
    response = client.get("/api/sensors")
    assert response.status_code == 200
    assert response.json() == station_out["sensors"]


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
