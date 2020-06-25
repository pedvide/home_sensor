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
    return db_stations


@router.get("/stations/{station_id}", response_model=schemas.Station)
def station(station_id: int, db: Session = Depends(get_db)):
    """Return the station id"""
    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")

    return db_station


@router.post("/stations", status_code=201, response_model=schemas.Station)
def create_station(
    station: schemas.StationCreate, response: Response, db: Session = Depends(get_db)
):
    """Body must contain hash(mac).
    Return 201 + station if it didn't exist.
    Return 200 + station if it already existed."""
    db_station = crud.get_station_by_token_and_location(
        db, token=station.token, location=station.location
    )

    if db_station:
        response.status_code = 200
    else:
        db_station = crud.create_station(db, station)

    response.headers["Location"] = str(db_station.id)
    return db_station


@router.put("/stations/{station_id}", status_code=204)
def change_station(
    station_id: int, new_station: schemas.StationCreate, db: Session = Depends(get_db),
):
    """Return 204 if change succeded"""
    db_station = crud.get_station(db, station_id)

    if not db_station:
        raise HTTPException(404, "Station not found")

    crud.change_station(db, db_station, new_station)


@router.get("/stations/{station_id}/measurements", response_model=List[schemas.Measurement])
def station_measurements(
    station_id: int, query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)
):
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    db_measurements = crud.get_station_measurements(
        db, station_id, **dataclasses.asdict(query_params)
    )
    return db_measurements


@router.post(
    "/stations/{station_id}/measurements",
    status_code=201,
    response_model=List[schemas.Measurement],
)
def create_measurement(
    station_id: int, measurements: List[schemas.MeasurementCreate], db: Session = Depends(get_db),
):
    """Return 201 + id."""
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    for num, measurement in enumerate(measurements):
        if not crud.get_sensor(db, measurement.sensor_id):
            raise HTTPException(404, "Sensor not found")
        if not crud.get_magnitude(db, measurement.magnitude_id):
            raise HTTPException(404, f"Magnitude not found in measurement {num}.")

    db_measurements = [
        crud.create_measurement(db, station_id, measurement) for measurement in measurements
    ]
    return db_measurements


## Sensors
@router.get("/sensors", response_model=List[schemas.Sensor])
def all_sensors(query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)):
    """Return all sensors that match the query"""
    db_sensors = crud.get_all_sensors(db, **dataclasses.asdict(query_params))
    return db_sensors


## Measurements
@router.get("/measurements", response_model=List[schemas.Measurement])
def all_measurements(
    query_params: ListQueryParameters = Depends(),
    order: str = "timestamp",
    db: Session = Depends(get_db),
):
    """Return all measurements that match the query"""
    db_measurements = crud.get_all_measurements(db, order=order, **dataclasses.asdict(query_params))
    return db_measurements
