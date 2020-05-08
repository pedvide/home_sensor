from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

import arrow

from typing import List

# from pprint import pprint

app = FastAPI()

timezone = "local"


unit_formatters = {
    "C": lambda value: f"{float(value):.2f}",
    "%": lambda value: f"{float(value):.1f}",
}


def parse_measurement_request(request_json: str) -> dict:
    """Parse request and return dict with measurement data"""
    date_fmt = "ddd YYYY-MM-DD HH:mm:ss"
    now = arrow.now(timezone)
    station_id = request_json.get("station_id", "unknown")
    sensor_id = request_json.get("sensor_id", "unknown")
    measurement_datetime = arrow.get(request_json.get("time")).to(timezone)
    measurement = {
        "station_id": station_id,
        "sensor_id": sensor_id,
        "measurement_time": f"{measurement_datetime.format(date_fmt)}",
        "measurement_time_offset": f"{measurement_datetime.humanize(now)}",
        "server_time": str(now.format(date_fmt)),
    }

    request_data = request_json.get("data")
    for item in request_data:
        name = item.get("name")
        value = item.get("value")
        unit = item.get("unit")
        if name and value:
            formatter = unit_formatters.get(unit, lambda value: str(value))
            fmt_value = formatter(value)
            measurement[name] = fmt_value

    return measurement


@app.get("/")
async def index():
    return "OK"
    # return render_template("index.html", **last_measurement)


## Sensors
class SensorIn(BaseModel):
    name: str

    measurement_names: List[str]
    measurement_units: List[str]


class Sensor(SensorIn):
    id: int


sensor0 = Sensor(id=0, name="am2320", measurement_names=["temp", "hum"], measurement_units=["C", "%"])
sensor1 = Sensor(id=1, name="accel", measurement_names=["ax", "ay", "az"], measurement_units=["m/s2"] * 3)
sensors = [sensor0, sensor1]


@app.get("/api/sensors/{id}", response_model=Sensor)
def sensor(id: int):
    if id not in range(len(sensor)):
        raise HTTPException(404, "Not found")
    return sensors[id]


@app.get("/api/sensors")
def all_sensor(id: int) -> List[Sensor]:
    return sensors


@app.post("/api/sensors", status_code=201, response_model=Sensor)
def create_sensor(sensor: SensorIn):
    """Body must contain hash(mac).
    Return 204 + station id in Location header if it didn't exist.
    Return 200 + station id in Location header or body if it already existed."""
    id = len(sensors)
    new_sensor = Sensor(id=id, **sensor.dict())
    sensors.append(new_sensor)
    return new_sensor


@app.delete("/api/sensors/{id}", status_code=204)
def delete_sensor(id: int):
    """Return 204 (No Content) on success"""
    if id not in range(len(sensors)):
        raise HTTPException(404, "Not found")
    sensors.pop(id)


## Stations
class StationIn(BaseModel):
    token: str
    location: str
    sensor_names: List[str]


class Station(StationIn):
    id: int


s0 = Station(id=12, token="asf3r23g2v", location="living room", sensor_names=["am2320"])
s1 = Station(id=13, token="g34yhnegwf", location="bedroom", sensor_names=["am2320"])
stations = {12: s0, 13: s1}


@app.get("/api/stations/{id}", response_model=Station)
def station(id: int):
    """Return the station id"""
    if id not in stations:
        raise HTTPException(404, "Not found")
    return stations[id]


@app.get("/api/stations", response_model=List[Station])
def all_stations(limit: int = 5, offset: int = 0):
    """Return all stations"""
    return list(stations.values())[offset : offset + limit]


@app.post("/api/stations", status_code=201, response_model=Station)
def create_station(station: StationIn, sensors: List[SensorIn]):
    """Body must contain hash(mac).
    Return 204 + station id in Location header if it didn't exist.
    Return 200 + station id in Location header or body if it already existed."""
    id = len(stations.keys())
    new_station = Station(id=id, **station.dict())
    stations.append(new_station)
    return new_station


@app.delete("/api/stations/{id}", status_code=204, response_class=Response)
def delete_station(id: int):
    """Return 204 (No Content) on success"""
    if id not in stations:
        raise HTTPException(404, "Not found")
    del stations[id]


@app.put("/api/stations/{id}/location", status_code=200, response_model=Station)
def change_station_position(id: int, location: str):
    """200 on success."""
    if id not in stations:
        raise HTTPException(404, "Not found")
    stations[id].location = location
    return stations[id]


@app.get("/api/stations/{id}/measurements")
def station_measurements(id: int, limit: int = 5, offset: int = 0):
    if id not in stations:
        raise HTTPException(404, "Not found")
    return [m for m in measurements if m.station_id == id][offset : offset + limit]


## Measurements
class SingleMeasurement(BaseModel):
    timestamp: int
    name: str
    unit: str
    value: str


class MeasurementIn(BaseModel):
    station_id: int
    sensor_name: str
    data: List[SingleMeasurement]


class Measurement(MeasurementIn):
    id: int


m0 = Measurement(
    id=0,
    station_id=12,
    sensor_name="tempsensor",
    data=[SingleMeasurement(timestamp=12353, name="temp", unit="C", value=23)],
)
m1 = Measurement(
    id=1,
    station_id=13,
    sensor_name="tempsensor",
    data=[SingleMeasurement(timestamp=12600, name="temp", unit="C", value=33)],
)
m2 = Measurement(
    id=2,
    station_id=13,
    sensor_name="am2320",
    data=[
        SingleMeasurement(timestamp=12600, name="temp", unit="C", value=33),
        SingleMeasurement(timestamp=12600, name="hum", unit="%", value=40),
    ],
)
measurements = [m0, m1, m2]


@app.get("/api/measurements/{id}", response_model=Measurement)
def measurement(id: int):
    """Return the measurement <id>"""
    if id not in range(len(measurements)):
        raise HTTPException(404, "Not found")
    return measurements[id]


@app.get(f"/api/measurements", response_model=List[Measurement])
def all_measurements(
    limit: int = 5, offset: int = 0, sort: str = None, before_date: str = None, after_date: str = None
):
    """Return all measurements that match the query"""
    return measurements[offset : offset + limit]


@app.post("/api/measurements", status_code=201, response_model=Measurement)
def create_measurement(measurement: MeasurementIn):
    """If one measurement return 201 + id.
    If several return 207 + list of ids."""
    id = len(measurements)
    new_meas = Measurement(id=id, **measurement.dict())
    measurements.append(new_meas)
    return new_meas


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
