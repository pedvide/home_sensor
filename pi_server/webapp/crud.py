from . import models, schemas
from .database import Session
from typing import List, Optional

# from pprint import pprint


# Magnitudes
def get_magnitude(db: Session, magnitude_id: int) -> Optional[models.Magnitude]:
    return db.query(models.Magnitude).get(magnitude_id)


def get_magnitude_by_name(db: Session, name: str) -> Optional[models.Magnitude]:
    return db.query(models.Magnitude).filter(models.Magnitude.name == name).one_or_none()


def create_magnitude(db: Session, magnitude: schemas.MagnitudeCreate) -> models.Magnitude:
    db_magnitude = models.Magnitude(**magnitude.dict())
    db.add(db_magnitude)
    db.commit()
    db.refresh(db_magnitude)
    return db_magnitude


# Sensors
def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    return db.query(models.Sensor).get(sensor_id)


def get_sensor_by_name(db: Session, name: str) -> Optional[models.Sensor]:
    return db.query(models.Sensor).filter(models.Sensor.name == name).one_or_none()


def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    db_sensor = models.Sensor(name=sensor.name)

    db_magnitudes = []
    for magnitude_in in sensor.magnitudes:
        magnitude = get_magnitude_by_name(db, magnitude_in.name)
        if not magnitude:
            magnitude = create_magnitude(db, magnitude_in)
        db_magnitudes.append(magnitude)
    db_sensor.magnitudes = db_magnitudes

    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


# Stations
def get_station(db: Session, station_id: int) -> Optional[models.Station]:
    return db.query(models.Station).get(station_id)


def get_station_by_token(db: Session, token: str) -> Optional[models.Station]:
    return db.query(models.Station).filter(models.Station.token == token).one_or_none()


def get_all_stations(db: Session, offset: int = 0, limit: int = 10) -> List[models.Station]:
    return db.query(models.Station).order_by(models.Station.id)[offset : offset + limit]


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    db_station = models.Station(location=station.location, token=station.token)

    db_sensors = []
    for sensor_in in station.sensors:
        sensor = get_sensor_by_name(db, sensor_in.name)
        if not sensor:
            sensor = create_sensor(db, sensor_in)
        db_sensors.append(sensor)
    db_station.sensors = db_sensors

    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


def change_station(
    db: Session, old_station: models.Station, new_station: schemas.StationCreate
) -> None:
    old_station.location = new_station.location

    db_sensors = []
    for sensor_in in new_station.sensors:
        sensor = get_sensor_by_name(db, sensor_in.name)
        if not sensor:
            sensor = create_sensor(db, sensor_in)
        db_sensors.append(sensor)
    old_station.sensors = db_sensors

    db.commit()


def delete_station(db: Session, station_id: int) -> None:
    db_station = db.query(models.Station).get(station_id)
    db.delete(db_station)
    db.commit()


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
def get_all_measurements(db: Session, offset: int = 0, limit: int = 10) -> List[models.Measurement]:
    return db.query(models.Measurement).all()[offset : offset + limit]


def create_measurement(
    db: Session, station_id: int, sensor_id: int, measurement: schemas.MeasurementCreate
) -> models.Measurement:
    db_measurement = models.Measurement(
        station_id=station_id, sensor_id=sensor_id, **measurement.dict()
    )

    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement
