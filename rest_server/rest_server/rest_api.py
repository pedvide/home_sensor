from fastapi import HTTPException, Response, Depends, APIRouter

from . import crud, schemas
from .database import Session, get_db, InfluxDBClient, get_influx_db

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
) -> schemas.Station:
    """Body must contain hash(mac).
    Return 201 + station if it didn't exist.
    Return 200 + station if it already existed."""
    db_station = crud.get_station_by_token_and_location(
        db, token=station.token, location=station.location
    )

    if db_station:
        crud.update_station(db, db_station, station)
        response.status_code = 200
    else:
        db_station = crud.create_station(db, station)

    response.headers["Location"] = str(db_station.id)
    return db_station


### Station sensors


@router.get("/stations/{station_id}/sensors", response_model=List[schemas.Sensor])
def station_sensors(
    station_id: int, query_params: ListQueryParameters = Depends(), db: Session = Depends(get_db)
):
    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")
    db_sensors = crud.get_station_sensors(db, db_station, **dataclasses.asdict(query_params))
    return db_sensors


@router.post("/stations/{station_id}/sensors", status_code=201, response_model=schemas.Sensor)
def create_station_sensor(
    station_id: int,
    sensor: schemas.SensorCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    """Sets the station's sensors to sensors"""

    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")

    # if sensor already exists in sensors, don't duplicate it
    db_sensor = crud.get_sensor_by_name_and_tag(db, sensor.name, sensor.tag)
    if not db_sensor:
        db_sensor = crud.create_sensor(db, sensor)

    # if sensor is already a sensor in this station, don't duplicate it either
    db_station_sensor = crud.get_station_sensor(db, db_station, db_sensor)
    if not db_station_sensor:
        db_station_sensor = crud.add_station_sensor(db, db_station, db_sensor)
    else:
        response.status_code = 200

    response.headers["Location"] = str(db_station_sensor.id)
    return db_station_sensor


@router.put("/stations/{station_id}/sensors", status_code=204)
def set_station_sensors(
    station_id: int,
    sensors: List[schemas.SensorCreate],
    response: Response,
    db: Session = Depends(get_db),
):
    """Sets the station's sensors to sensors"""

    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")

    old_sensor_names = [db_sensor.name for db_sensor in db_station.sensors]
    new_sensor_names = [sensor.name for sensor in sensors]
    sensor_names_add = set(new_sensor_names).difference(set(old_sensor_names))
    sensors_add = [sensor for sensor in sensors if sensor.name in sensor_names_add]
    db_sensor_names_delete = set(old_sensor_names).difference(set(new_sensor_names))
    db_sensors_delete = [
        sensor
        for sensor in crud.get_station_sensors(db, db_station)
        if sensor.name in db_sensor_names_delete
    ]

    for sensor in sensors_add:
        db_sensor = crud.get_sensor_by_name_and_tag(db, sensor.name, sensor.tag)
        if db_sensor:
            crud.add_station_sensor(db, db_station, db_sensor)
        else:
            crud.create_station_sensor(db, db_station, sensor)

    for db_sensor in db_sensors_delete:
        crud.delete_station_sensor(db, db_station, db_sensor)


@router.get("/stations/{station_id}/sensors/{sensor_id}", response_model=schemas.Sensor)
def station_sensor(station_id: int, sensor_id: int, db: Session = Depends(get_db)):
    db_station = crud.get_station(db, station_id)
    if not db_station:
        raise HTTPException(404, "Station not found")
    db_sensor = crud.get_sensor(db, sensor_id)
    if not db_sensor:
        raise HTTPException(404, "Sensor not found")
    db_sensor = crud.get_station_sensor(db, db_station, db_sensor)
    return db_sensor


### Station measurements


@router.get("/stations/{station_id}/measurements", response_model=List[schemas.Measurement])
def station_measurements(
    station_id: int,
    query_params: ListQueryParameters = Depends(),
    db: Session = Depends(get_db),
    db_influx: InfluxDBClient = Depends(get_influx_db),
):
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    db_measurements = crud.get_station_measurements(
        db, db_influx, station_id, **dataclasses.asdict(query_params)
    )
    return db_measurements


@router.post(
    "/stations/{station_id}/measurements",
    status_code=201,
    response_model=List[schemas.Measurement],
)
def create_measurement(
    station_id: int,
    measurements: List[schemas.MeasurementCreate],
    db: Session = Depends(get_db),
    db_influx: InfluxDBClient = Depends(get_influx_db),
):
    """Return 201 + id."""
    if not crud.get_station(db, station_id):
        raise HTTPException(404, "Station not found")
    for num, measurement in enumerate(measurements):
        if not crud.get_sensor(db, measurement.sensor_id):
            raise HTTPException(404, "Sensor not found")
        if not crud.get_magnitude(db, measurement.magnitude_id):
            raise HTTPException(404, f"Magnitude not found in measurement {num}.")

    db_measurements = crud.create_measurements(db, db_influx, station_id, measurements)
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
    db: Session = Depends(get_db),
    db_influx: InfluxDBClient = Depends(get_influx_db),
):
    """Return all measurements that match the query"""
    db_measurements = crud.get_all_measurements(db, db_influx, **dataclasses.asdict(query_params))
    return db_measurements
