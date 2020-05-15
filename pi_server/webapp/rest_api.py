from fastapi import HTTPException, Response, Depends, APIRouter

from . import crud, schemas
from .database import Session, get_db

from typing import List
import dataclasses

router = APIRouter()


@dataclasses.dataclass
class ListQueryParameters:
    offset: int = 0
    limit: int = 5


## Stations
@router.get("/stations", response_model=List[schemas.Station])
def all_stations(query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)):
    """Return all stations"""
    db_stations = crud.get_all_stations(db, **dataclasses.asdict(query_params))
    return [crud.db_station_to_schema(db, db_station) for db_station in db_stations]


@router.post("/stations", status_code=201, response_model=schemas.Station)
def create_station(
    station: schemas.StationCreate, response: Response, db: Session = Depends(get_db)
):
    """Body must contain hash(mac).
    Return 201 + station if it didn't exist.
    Return 200 + station if it already existed."""
    db_station = crud.get_station_by_token(db, token=station.token)
    if db_station:
        response.status_code = 200
        station_out = crud.db_station_to_schema(db, db_station)
        return station_out

    db_station = crud.create_station(db, station)
    station_out = crud.db_station_to_schema(db, db_station)
    return station_out


@router.get("/stations/{station_id}", response_model=schemas.Station)
def station(station_id: int, db: Session = Depends(get_db)):
    """Return the station id"""
    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")

    station_out = crud.db_station_to_schema(db, db_station)
    return station_out


## TODO: Add DELETE/PUT stations/ to delete/update localtion and sensors


@router.get("/stations/{station_id}/measurements", response_model=List[schemas.Measurement])
def station_measurements(
    station_id: int, query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)
):
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    db_measurements = crud.get_station_measurements(
        db, station_id, **dataclasses.asdict(query_params)
    )
    measurements_out = [
        crud.db_measurement_to_schema(db, db_measurement) for db_measurement in db_measurements
    ]
    return measurements_out


@router.post(
    "/stations/{station_id}/sensors/{sensor_id}/measurements",
    status_code=201,
    response_model=List[schemas.Measurement],
)
def create_measurement(
    station_id: int,
    sensor_id: int,
    measurements: List[schemas.MeasurementCreate],
    db: Session = Depends(get_db),
):
    """Return 201 + id."""
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    if not crud.get_sensor(db, sensor_id):
        raise HTTPException(404, "Sensor not found")

    db_measurements = [
        crud.create_measurement(db, station_id, sensor_id, measurement)
        for measurement in measurements
    ]
    measurements_out = [
        crud.db_measurement_to_schema(db, db_measurement) for db_measurement in db_measurements
    ]

    return measurements_out


## Measurements
@router.get(f"/measurements", response_model=List[schemas.Measurement])
def all_measurements(query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)):
    """Return all measurements that match the query"""
    db_measurements = crud.get_all_measurements(db, **dataclasses.asdict(query_params))
    return [crud.db_measurement_to_schema(db, db_measurement) for db_measurement in db_measurements]
