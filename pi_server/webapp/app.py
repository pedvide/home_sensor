from fastapi import FastAPI, Request

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import arrow

from . import rest_api

# from pprint import pprint

app = FastAPI()
app.include_router(rest_api.router, prefix="/api")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

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


last_measurement = {
    "station_id": 0,
    "sensor_id": 0,
    "time": 1589231767,
    "data": [{"name": "temp", "unit": "C", "value": "23.5"}, {"name": "hum", "unit": "%", "value": "40"}],
}


@app.get("/")
async def index(request: Request):
    parsed_last_measurement = parse_measurement_request(last_measurement)
    return templates.TemplateResponse("index.html", {"request": request, **parsed_last_measurement})


# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
