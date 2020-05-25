from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import arrow

from . import rest_api, crud, schemas
from .database import engine, get_db, Session
from . import models

models.Base.metadata.create_all(bind=engine)

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


def parse_measurement_request(request_json: dict) -> dict:
    """Parse request and return dict with measurement data"""
    date_fmt = "ddd YYYY-MM-DD HH:mm:ss"
    now = arrow.now(timezone)
    station = request_json.get("station").get("location")
    sensor = request_json.get("sensor").get("name")
    measurement_datetime = arrow.get(request_json.get("time")).to(timezone)
    measurement = {
        "station": str(station),
        "sensor": str(sensor),
        "measurement_time": f"{measurement_datetime.format(date_fmt)}",
        "measurement_time_offset": f"{measurement_datetime.humanize(now)}",
        "server_time": str(now.format(date_fmt)),
    }

    measurement["name"] = request_json.get("magnitude").get("name")
    measurement["unit"] = request_json.get("magnitude").get("unit")
    value = request_json.get("value")
    formatter = unit_formatters.get(measurement["unit"], lambda value: str(value))
    fmt_value = formatter(value)
    measurement["value"] = fmt_value
    return measurement


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    db_measurement = crud.get_all_measurements(db, limit=1)
    measurement = schemas.Measurement.from_orm(db_measurement[0]) if db_measurement else {}
    parsed_last_measurement = (
        parse_measurement_request(measurement.dict()) if db_measurement else {}
    )
    return templates.TemplateResponse("index.html", {"request": request, **parsed_last_measurement})


# redirect port 8080 to 80 (only available to root) with:
# sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-ports 8080
# sudo iptables-save
# run locally uvicorn webapp.app:app --reload
# run in the pi with uvicorn webapp.app:app --reload --port 8080 --host 0.0.0.0
