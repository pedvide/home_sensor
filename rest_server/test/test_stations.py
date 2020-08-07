"""Test station endpoints /api/stations..."""


def test_get_wrong_station(client, db_session):
    response = client.get("/api/stations/0")
    assert response.status_code == 404
    assert "Station not found" in response.json().values()


def test_create_get_one_station(client, db_session, station_one):
    station_in, station_out = station_one

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


def test_create_get_two_stations(client, db_session, station_one, station_two):

    station1_in, station1_out = station_one
    station2_in, station2_out = station_two

    client.post("/api/stations", json=station1_in)

    response = client.post("/api/stations", json=station2_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "2"
    assert response.json() == station2_out

    response = client.get("/api/stations/1")
    assert response.status_code == 200
    assert response.json() == station1_out

    response = client.get("/api/stations/2")
    assert response.status_code == 200
    assert response.json() == station2_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station1_out, station2_out]

    response = client.get("/api/stations?offset=0&limit=1")
    assert response.status_code == 200
    assert response.json() == [station1_out]

    response = client.get("/api/stations?offset=0&limit=2")
    assert response.status_code == 200
    assert response.json() == [station1_out, station2_out]


def test_create_same_station_twice(client, db_session, station_one):
    station1_in, station1_out = station_one

    # first
    client.post("/api/stations", json=station1_in)

    # repeat POST should return first resource + 200
    response = client.post("/api/stations", json=station1_in)
    assert response.status_code == 200
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station1_out

    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [station1_out]


def test_create_station_with_sensors(client, db_session, station_one, sensor_one):
    station_in, station_out = station_one
    sensor_in, sensor_out = sensor_one
    station_in["sensors"] = [sensor_in]
    station_out["sensors"] = [sensor_out]

    response = client.post("/api/stations", json=station_in)
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"] == "1"
    assert response.json() == station_out

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor_out]

    response = client.get("/api/stations/1/sensors/1")
    assert response.status_code == 200
    assert response.json() == sensor_out


def test_create_get_station_sensors(client, db_session, station_one, sensor_one):
    station_in, station_out = station_one
    sensor_in, sensor_out = sensor_one

    client.post("/api/stations", json=station_in)

    response = client.put("/api/stations/1/sensors", json=[sensor_in])
    assert response.status_code == 204

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor_out]

    response = client.get("/api/stations/1/sensors/1")
    assert response.status_code == 200
    assert response.json() == sensor_out


def test_create_get_two_station_sensors(client, db_session, station_one, sensor_one, sensor_two):
    station_in, station_out = station_one
    sensor1_in, sensor1_out = sensor_one
    sensor2_in, sensor2_out = sensor_two

    client.post("/api/stations", json=station_in)

    response = client.put("/api/stations/1/sensors", json=[sensor1_in, sensor2_in])
    assert response.status_code == 204

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor1_out, sensor2_out]

    response = client.get("/api/stations/1/sensors/1")
    assert response.status_code == 200
    assert response.json() == sensor1_out

    response = client.get("/api/stations/1/sensors/2")
    assert response.status_code == 200
    assert response.json() == sensor2_out


def test_create_same_station_sensor_twice(client, db_session, station_one, sensor_one):
    station_in, station_out = station_one
    sensor1_in, sensor1_out = sensor_one

    client.post("/api/stations", json=station_in)
    client.put("/api/stations/1/sensors", json=[sensor1_in])

    # PUT is idempotent, so it shouldn't duplicate
    response = client.put("/api/stations/1/sensors", json=[sensor1_in])
    assert response.status_code == 204

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor1_out]


def test_create_two_stations_same_sensor(client, db_session, station_one, station_two, sensor_one):
    from rest_server import models

    station1_in, station1_out = station_one
    station2_in, station2_out = station_two
    sensor1_in, sensor1_out = sensor_one

    client.post("/api/stations", json=station1_in)
    client.put("/api/stations/1/sensors", json=[sensor1_in])

    print(db_session.query(models.Station).all())
    print(db_session.query(models.Sensor).all())
    print(db_session.query(models.StationSensor).all())

    # create new station with the same sensor
    client.post("/api/stations", json=station2_in)
    response = client.put("/api/stations/2/sensors", json=[sensor1_in])
    assert response.status_code == 204

    print(db_session.query(models.Station).all())
    print(db_session.query(models.Sensor).all())
    print(db_session.query(models.StationSensor).all())

    response = client.get("/api/stations/1/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor1_out]

    response = client.get("/api/stations/2/sensors")
    assert response.status_code == 200
    assert response.json() == [sensor1_out]
