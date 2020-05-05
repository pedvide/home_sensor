from flask import Flask
from flask import render_template
from flask import request
import arrow

from typing import List

# from pprint import pprint

app = Flask(__name__)

last_request = None
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


@app.route("/")
def index():
    last_measurement = parse_measurement_request(last_request)
    return render_template("index.html", **last_measurement)


@app.route("/api/upload_data", method="POST")
def upload_data():
    global last_request
    content = request.get_json(silent=True)
    last_request = content
    return {"success": True}, 200


@app.route("/api/last_measurement")
def last_measurement():
    if not last_request:
        return "Not ready", 404
    return parse_measurement_request(last_request)


# New API
class Measurement:
    id: int

    station_id: int
    sensor_name: str

    timestamp: int
    name: str
    unit: str
    value: str


class Station:
    id: int
    token: str
    location: str
    sensor_names: List[str]


class Sensor:
    id: int
    name: str

    measurement_names: List[str]
    measurement_units: List[str]


## Measurements
measurement_query = {
    "limit": "<limit>",  # 10
    "offset": "<offset>",  # 0
    "sort": "<sort>",  # -measurement_date
    "before_date": "<before_date>",  # now
    "after_date": "<after_date>",  # 1 day ago
}
query_str = "&".join(f"{key}={value}" for key, value in measurement_query.items())


@app.route("/api/measurements/<id>")
def measurement(id: int) -> Measurement:
    """Return the measurement <id>"""
    pass


@app.route(f"/api/measurements?{query_str}")
def all_measurements(limit, offset, sort, before_date, after_date) -> List[Measurement]:
    """Return all measurements that match the query"""
    pass


@app.route("/api/measurements", method="POST")
def create_measurement():
    """If one measurement return 201 + id.
    If several return 207 + list of ids."""
    pass


## Stations
@app.route("/api/stations/<id>")
def station(id: int) -> Station:
    """Return the station <id>"""
    pass


@app.route("/api/stations")
def all_stations(id: int) -> List[Station]:
    """Return all stations"""
    pass


@app.route("/api/stations", method="POST")
def create_station():
    """Body must contain hash(mac).
    Return 204 + station id in Location header if it didn't exist.
    Return 200 + station id in Location header or body if it already existed."""
    pass


@app.route("/api/stations/<id>", method="DELETE")
def delete_station(id: int):
    """Return 204 (No Content) on success"""
    pass


@app.route("/api/stations/<id>/position", method="PUT")
def change_station_position(id: int):
    """200 on success."""
    pass


@app.route(f"/api/stations/<id>/measurements?{query_str}")
def station_measurements(limit, offset, sort, before_date, after_date):
    pass


## Sensors
@app.route("/api/sensors/<id>")
def sensor(id: int) -> Sensor:
    pass


@app.route("/api/sensors")
def all_sensor(id: int) -> List[Sensor]:
    pass


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
