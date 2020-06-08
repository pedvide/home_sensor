from . import models, schemas
from .database import Session
from typing import List, Optional
from datetime import datetime

# from pprint import pprint


# Magnitudes
def get_magnitude(db: Session, magnitude_id: int) -> Optional[models.Magnitude]:
    return db.query(models.Magnitude).get(magnitude_id)


def create_magnitude(db: Session, magnitude: schemas.MagnitudeCreate) -> models.Magnitude:
    db_magnitude = models.Magnitude(**magnitude.dict())
    db.add(db_magnitude)
    db.commit()
    db.refresh(db_magnitude)
    return db_magnitude


# Sensors
def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    return db.query(models.Sensor).get(sensor_id)


def get_all_sensors(db: Session, offset: int = 0, limit: int = 10) -> List[models.Sensor]:
    return db.query(models.Sensor).order_by(models.Sensor.id)[offset : offset + limit]


def get_sensor_by_name(db: Session, name: str) -> Optional[models.Sensor]:
    return db.query(models.Sensor).filter(models.Sensor.name == name).one_or_none()


def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    db_sensor = models.Sensor(name=sensor.name)

    db_magnitudes = [create_magnitude(db, magnitude_in) for magnitude_in in sensor.magnitudes]
    db_sensor.magnitudes = db_magnitudes

    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


# Stations
def get_station(db: Session, station_id: int) -> Optional[models.Station]:
    return (
        db.query(models.Station)
        .filter(models.Station.id == station_id)
        .filter(models.Station.valid_until.is_(None))
        .one_or_none()
    )


def get_station_by_token(db: Session, token: str) -> Optional[models.Station]:
    return (
        db.query(models.Station)
        .filter(models.Station.token == token)
        .filter(models.Station.valid_until.is_(None))
        .one_or_none()
    )


def get_all_stations(db: Session, offset: int = 0, limit: int = 10) -> List[models.Station]:
    return (
        db.query(models.Station)
        .filter(models.Station.valid_until.is_(None))
        .order_by(models.Station.id)
        .limit(limit)
        .offset(offset)
        .all()
    )


def _create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    """Create and return a station but don't add it to the DB."""

    db_station = models.Station(location=station.location, token=station.token)

    db_sensors = []
    for sensor_in in station.sensors:
        sensor = get_sensor_by_name(db, sensor_in.name)
        if not sensor:
            sensor = create_sensor(db, sensor_in)
        db_sensors.append(sensor)
    db_station.sensors = db_sensors

    return db_station


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:

    db_station = _create_station(db, station)
    db.add(db_station)
    db.commit()
    db.refresh(db_station)

    return db_station


def change_station(
    db: Session, db_old_station: models.Station, new_station: schemas.StationCreate
) -> None:
    # create a new station but with the same id
    db_new_station = _create_station(db, new_station)
    db_old_station.valid_until = datetime.now()
    db_new_station.id = db_old_station.id

    db.add(db_new_station)
    db.commit()
    db.refresh(db_new_station)

    return db_new_station


def get_station_measurements(
    db: Session, station_id: int, offset: int = 0, limit: int = 10
) -> List[models.Measurement]:
    return (
        db.query(models.Station)
        .filter(models.Station.id == station_id)
        .one()
        .measurements[offset : offset + limit]
    )


# Measurements
def get_all_measurements(
    db: Session, order: str = "timestamp", offset: int = 0, limit: int = 10
) -> List[models.Measurement]:
    return (
        db.query(models.Measurement)
        .order_by(getattr(models.Measurement, order, "timestamp").desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def create_measurement(
    db: Session, station_id: int, measurement: schemas.MeasurementCreate
) -> models.Measurement:
    db_measurement = models.Measurement(station_id=station_id, **measurement.dict())

    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement
