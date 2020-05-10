from fastapi import FastAPI

import arrow

from . import rest_api

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


app.include_router(rest_api.router, prefix="/api")

# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
