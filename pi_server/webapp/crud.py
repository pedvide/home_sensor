from . import models, schemas
from .database import Session
from typing import List, Optional

# from pprint import pprint


def get_station(db: Session, station_id: int) -> Optional[models.Station]:
    return db["stations"].get(station_id)


def get_station_by_token(db: Session, token: str) -> Optional[models.Station]:
    stations = [station for station_id, station in db["stations"].items() if station.token == token]
    return stations[0] if stations else None


def get_all_stations(db: Session, offset: int = 0, limit: int = 10) -> List[models.Station]:
    return list(db["stations"].values())[offset : offset + limit]


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    station_id = len(db["stations"].keys())
    new_station = models.Station(id=station_id, sensors=[], location=station.location, token=station.token)
    new_sensors = []
    for sensor in station.sensors:
        sensor_id = len(db["sensors"])
        new_sensor = models.Sensor(id=sensor_id, station_id=station_id, **sensor.dict())
        db["sensors"][sensor_id] = new_sensor
        new_sensors.append(new_sensor)
    new_station.sensors = new_sensors
    db["stations"][station_id] = new_station
    return new_station


def delete_station(db: Session, station_id: int) -> None:
    del db["stations"][station_id]


def get_station_measurements(
    db: Session, station_id: int, offset: int = 0, limit: int = 10
) -> List[models.Measurement]:
    return [m for m in db["measurements"] if m.station_id == station_id][offset : offset + limit]


def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    return db["sensor"].get(sensor_id)


def get_all_measurements(db: Session, offset: int = 0, limit: int = 10):
    return list(db["measurements"].values())[offset : offset + limit]


def create_measurement(
    db: Session, station_id: int, sensor_id: int, measurement: schemas.MeasurementCreate
) -> models.Measurement:
    meas_id = len(db["measurements"])
    new_meas = models.Measurement(
        id=meas_id, station_id=station_id, sensor_id=sensor_id, **measurement.dict()
    )
    db["measurements"][meas_id] = new_meas
    return new_meas
