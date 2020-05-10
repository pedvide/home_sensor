from fastapi.testclient import TestClient

from webapp import app, get_db

## Testing
client = TestClient(app)


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "OK"


def test_add_station():
    sensor0 = dict(name="am2320", magnitude_names=["temp", "hum"], magnitude_units=["C", "%"])
    station = dict(token="asf3r23g2v", location="living room", sensors=[sensor0])

    station_out = dict(id=0, token="asf3r23g2v", location="living room", sensor_ids=[0])

    with get_db:
        response = client.post("/api/stations", json=station)
    assert response.status_code == 201
    assert response.json() == station_out


def test_add_station_two_sensors():
    sensor0 = dict(name="am2320", magnitude_names=["temp", "hum"], magnitude_units=["C", "%"])
    sensor1 = dict(name="temponly", magnitude_names=["temp"], magnitude_units=["C"])
    station = dict(token="sfsdgsds", location="bedroom", sensors=[sensor0, sensor1])

    station_out = dict(id=0, token="sfsdgsds", location="bedroom", sensor_ids=[0, 1])

    with get_db:
        response = client.post("/api/stations", json=station)
    assert response.status_code == 201
    assert response.json() == station_out


def test_get_stations():
    sensor0 = dict(name="am2320", magnitude_names=["temp", "hum"], magnitude_units=["C", "%"])
    station0 = dict(token="asf3r23g2v", location="living room", sensors=[sensor0])
    client.post("/api/stations", json=station0)

    sensor1 = dict(name="temponly", magnitude_names=["temp"], magnitude_units=["C"])
    station1 = dict(token="sfsdgsds", location="bedroom", sensors=[sensor0, sensor1])
    client.post("/api/stations", json=station1)

    # station0_out = dict(id=0, token="asf3r23g2v", location="living room", sensor_ids=[0])
    # station1_out = dict(id=1, token="sfsdgsds", location="bedroom", sensor_ids=[1, 2])

    with get_db as db:
        print(db["stations"])
        response = client.get("/api/stations")
    assert response.status_code == 200
    # assert response.json() == station_out


"""
s0 = Station(id=12, token="asf3r23g2v", location="living room")
s1 = Station(id=13, token="g34yhnegwf", location="bedroom")
stations = {12: s0, 13: s1}

sensor0 = Sensor(
    id=0, station_id=12, name="am2320", magnitude_names=["temp", "hum"], magnitude_units=["C", "%"]
)
sensor1 = Sensor(id=1, station_id=13, name="temponly", magnitude_names=["temp"], magnitude_units=["C"])
sensors = {0: sensor0, 1: sensor1}
s0.sensors = [
    sensor0,
]
s1.sensors = [
    sensor1,
]


m0 = Measurement(
    id=0,
    station_id=13,
    sensor_id=1,
    data=[SingleMeasurement(id=0, timestamp=12353, name="temp", unit="C", value=23)],
)
m1 = Measurement(
    id=1,
    station_id=13,
    sensor_id=1,
    data=[SingleMeasurement(id=1, timestamp=12600, name="temp", unit="C", value=33)],
)
m2 = Measurement(
    id=2,
    station_id=12,
    sensor_id=0,
    data=[
        SingleMeasurement(id=2, timestamp=12600, name="temp", unit="C", value=33),
        SingleMeasurement(id=3, timestamp=12600, name="hum", unit="%", value=40),
    ],
)
measurements = {0: m0, 1: m1, 2: m2}
"""
