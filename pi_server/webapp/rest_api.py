from fastapi import HTTPException, Response, Depends, APIRouter

from . import crud, schemas
from .database import Session, get_db

from typing import List

router = APIRouter()

## Stations
@router.get("/stations", response_model=List[schemas.Station])
def all_stations(limit: int = 5, offset: int = 0, db: Session = Depends(get_db)):
    """Return all stations"""
    return crud.get_all_stations(db, offset, limit)


@router.post("/stations", status_code=201, response_model=schemas.Station)
def create_station(station: schemas.StationCreate, db: Session = Depends(get_db)):
    """Body must contain hash(mac).
    Return 201 + station if it didn't exist.
    Return 200 + station if it already existed."""
    db_station = crud.get_station_by_token(db, token=station.token)
    if db_station:
        return Response(db_station, status_code=200)
    return crud.create_station(db, station)


@router.get("/stations/{station_id}", response_model=schemas.Station)
def station(station_id: int, db: Session = Depends(get_db)):
    """Return the station id"""
    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")
    return db_station


@router.delete("/stations/{station_id}", status_code=204, response_class=Response)
def delete_station(station_id: int, db: Session = Depends(get_db)):
    """Return 204 (No Content) on success"""
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    crud.delete_station(db, station_id)


## TODO: Add PUT api/stations/ to update localtion and sensors


@router.get("/stations/{station_id}/measurements", response_model=schemas.Measurement)
def station_measurements(station_id: int, limit: int = 5, offset: int = 0, db: Session = Depends(get_db)):
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    return crud.get_station_measurements(db, station_id)


@router.post(
    "/stations/{station_id}/sensors/{sensor_id}/measurements",
    status_code=201,
    response_model=schemas.Measurement,
)
def create_measurement(
    station_id: int, sensor_id: int, measurement: schemas.MeasurementCreate, db: Session = Depends(get_db)
):
    """If one measurement return 201 + id.
    If several return 207 + list of ids."""
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    if not crud.get_sensor(db, sensor_id):
        raise HTTPException(404, "Sensor not found")

    db_meas = crud.create_measurement(db, station_id, sensor_id, measurement)
    return db_meas


## Measurements
@router.get(f"/measurements", response_model=List[schemas.Measurement])
def all_measurements(limit: int = 5, offset: int = 0, db: Session = Depends(get_db)):
    """Return all measurements that match the query"""
    return crud.get_all_measurements(db, offset, limit)
