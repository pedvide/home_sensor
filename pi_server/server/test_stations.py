"""Test station endpoints /api/stations..."""


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


def test_station_no_sensors(client, db_session, station_zero):
    station_in, station_out = station_zero
    station_in["sensors"] = []
    station_out["sensors"] = []

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


def test_station_sensors(client, db_session, station_zero):
    station_in, station_out = station_zero
    sensors_out = station_out["sensors"]

    response = client.post("/api/stations", json=station_in)

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == sensors_out

    ids = [sensor["id"] for sensor in sensors_out]

    for num, sensor_id in enumerate(ids):
        response = client.get(f"/api/stations/1/sensors/{sensor_id}")
        assert response.status_code == 200
        assert response.json() == sensors_out[num]


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


def test_modify_station_sensors(client, db_session, station_zero, station_one):
    """Create a station1, then set it to have station0's sensors"""
    station0_in, station0_out = station_zero
    station1_in, station1_out = station_one

    modified_station_in = dict()
    modified_station_in["token"] = station1_in["token"]
    modified_station_in["location"] = station1_in["location"]
    modified_station_in["sensors"] = station0_in["sensors"]
    modified_station_out = dict()
    modified_station_out["id"] = 1
    modified_station_out["token"] = station1_out["token"]
    modified_station_out["location"] = station1_out["location"]
    modified_station_out["sensors"] = station0_out["sensors"]

    # create station first
    response = client.post("/api/stations", json=station1_in)

    # PUT with updated sensors
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
