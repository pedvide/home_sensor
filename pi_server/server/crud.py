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
    return db.query(models.Sensor).order_by(models.Sensor.id).limit(limit).offset(offset).all()


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
    return db.query(models.Station).get(station_id)


def get_station_by_token_and_location(
    db: Session, token: str, location: str
) -> Optional[models.Station]:
    return (
        db.query(models.Station)
        .filter(models.Station.token == token)
        .filter(models.Station.location == location)
        .one_or_none()
    )


def get_all_stations(db: Session, offset: int = 0, limit: int = 10) -> List[models.Station]:
    return db.query(models.Station).order_by(models.Station.id).limit(limit).offset(offset).all()


def _create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    """Create and return a station but don't add it to the DB."""
    db_station = models.Station(location=station.location, token=station.token, sensors=[])

    for sensor_in in station.sensors:
        sensor = get_sensor_by_name(db, sensor_in.name)
        if not sensor:
            sensor = create_sensor(db, sensor_in)
        db_station.add_sensor(sensor)

    return db_station


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    db_station = _create_station(db, station)
    db.add(db_station)
    db.commit()
    db.refresh(db_station)

    return db_station


def remove_sensor_from_station(
    db: Session, sensor: schemas.Sensor, station: schemas.Station
) -> None:
    station_sensor = (
        db.query(models.StationSensor)
        .filter(models.StationSensor.sensor == sensor, models.StationSensor.station == station)
        .one()
    )
    station_sensor.valid_until = datetime.now()
    db.commit()


def change_station(
    db: Session, db_station: models.Station, new_station: schemas.StationCreate
) -> None:
    """Change the station sensors to match new_station's"""
    # create non-existing sensors
    new_sensors = []
    for new_sensor in new_station.sensors:
        sensor = get_sensor_by_name(db, name=new_sensor.name)
        if not sensor:
            sensor = create_sensor(db, new_sensor)
            new_sensors.append(sensor)

    # remove current sensors that are not in new_station.sensors
    sensor_names = {sensor.name for sensor in new_station.sensors}
    current_sensor_names = {sensor.name for sensor in db_station.sensors}
    sensor_names_to_delete = current_sensor_names.difference(sensor_names)
    sensors_to_delete = [get_sensor_by_name(db, name=name) for name in sensor_names_to_delete]
    for db_sensor in sensors_to_delete:
        remove_sensor_from_station(db, db_sensor, db_station)

    db_station.add_sensors(new_sensors)
    db.commit()
    db.refresh(db_station)

    return db_station


def get_station_sensors(
    db: Session, station_id: int, offset: int = 0, limit: int = 10
) -> List[models.Sensor]:
    return db.query(models.Station).get(station_id).sensors[offset:limit]


def get_station_measurements(
    db: Session, station_id: int, order: str = "timestamp", offset: int = 0, limit: int = 10
) -> List[models.Measurement]:
    return (
        db.query(models.Station)
        .get(station_id)
        .measurements.order_by(getattr(models.Measurement, order, "timestamp").desc())
        .limit(limit)
        .offset(offset)
        .all()
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
