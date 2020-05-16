from . import models, schemas
from .database import Session
from typing import List, Optional

# from pprint import pprint


# Translate from models to schemas
def db_magnitude_to_schema(db: Session, db_magnitude: models.Magnitude) -> schemas.Magnitude:
    return schemas.Magnitude.from_orm(db_magnitude)


def db_sensor_to_schema(db: Session, db_sensor: models.Sensor) -> schemas.Sensor:
    db_magnitudes = [get_magnitude(db, magnitude_id) for magnitude_id in db_sensor.magnitude_ids]
    magnitudes_out = [db_magnitude_to_schema(db, db_magnitude) for db_magnitude in db_magnitudes]
    sensor_out = {"id": db_sensor.id, "name": db_sensor.name, "magnitudes": magnitudes_out}
    return schemas.Sensor(**sensor_out)


def db_station_to_schema(db: Session, db_station: models.Station) -> schemas.Station:
    db_sensors = [get_sensor(db, sensor_id) for sensor_id in db_station.sensor_ids]
    sensors_out = [db_sensor_to_schema(db, db_sensor) for db_sensor in db_sensors]
    station_out = {
        "id": db_station.id,
        "token": db_station.token,
        "location": db_station.location,
        "sensors": sensors_out,
    }
    return schemas.Station(**station_out)


def db_measurement_to_schema(
    db: Session, db_measurement: models.Measurement
) -> schemas.Measurement:
    sensor = db_sensor_to_schema(db, get_sensor(db, db_measurement.sensor_id))
    station = db_station_to_schema(db, get_station(db, db_measurement.station_id))
    magnitude = db_magnitude_to_schema(db, get_magnitude(db, db_measurement.magnitude_id))
    measurement_out = {
        "id": db_measurement.id,
        "timestamp": db_measurement.timestamp,
        "value": db_measurement.value,
        "sensor": sensor,
        "station": station,
        "magnitude": magnitude,
    }
    return schemas.Measurement(**measurement_out)


# Magnitudes
def get_magnitude(db: Session, magnitude_id: int) -> Optional[models.Magnitude]:
    return db["magnitudes"].get(magnitude_id)


def get_magnitude_by_name(db: Session, name: str) -> Optional[models.Magnitude]:
    magnitudes = [
        magnitude for magnitude_id, magnitude in db["magnitudes"].items() if magnitude.name == name
    ]
    return magnitudes[0] if magnitudes else None


def create_magnitude(db: Session, magnitude: schemas.MagnitudeCreate) -> models.Magnitude:
    magnitude_id = len(db["magnitudes"])
    new_magnitude = models.Magnitude(id=magnitude_id, **magnitude.dict())
    db["magnitudes"][magnitude_id] = new_magnitude
    return new_magnitude


# Sensors
def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    return db["sensors"].get(sensor_id)


def get_sensor_by_name(db: Session, name: str) -> Optional[models.Sensor]:
    sensors = [sensor for sensor_id, sensor in db["sensors"].items() if sensor.name == name]
    return sensors[0] if sensors else None


def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    sensor_id = len(db["sensors"])
    new_sensor = models.Sensor(id=sensor_id, name=sensor.name, magnitude_ids=[])
    new_magnitude_ids = []
    for magnitude_in in sensor.magnitudes:
        magnitude = get_magnitude_by_name(db, magnitude_in.name)
        if not magnitude:
            magnitude = create_magnitude(db, magnitude_in)
        new_magnitude_ids.append(magnitude.id)
    new_sensor.magnitude_ids = new_magnitude_ids
    db["sensors"][sensor_id] = new_sensor
    return new_sensor


# Stations
def get_station(db: Session, station_id: int) -> Optional[models.Station]:
    return db["stations"].get(station_id)


def get_station_by_token(db: Session, token: str) -> Optional[models.Station]:
    stations = [station for station_id, station in db["stations"].items() if station.token == token]
    return stations[0] if stations else None


def get_all_stations(db: Session, offset: int = 0, limit: int = 10) -> List[models.Station]:
    return list(db["stations"].values())[offset : offset + limit]


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    station_id = len(db["stations"].keys())
    new_station = models.Station(
        id=station_id, sensor_ids=[], location=station.location, token=station.token
    )
    new_sensor_ids = []
    for sensor_in in station.sensors:
        sensor = get_sensor_by_name(db, sensor_in.name)
        if not sensor:
            sensor = create_sensor(db, sensor_in)
        new_sensor_ids.append(sensor.id)
    new_station.sensor_ids = new_sensor_ids
    db["stations"][station_id] = new_station
    return new_station


def delete_station(db: Session, station_id: int) -> None:
    del db["stations"][station_id]


def get_station_measurements(
    db: Session, station_id: int, offset: int = 0, limit: int = 10
) -> List[models.Measurement]:
    return [m for m_id, m in db["measurements"].items() if m.station_id == station_id][
        offset : offset + limit
    ]


# Measurements
def get_all_measurements(db: Session, offset: int = 0, limit: int = 10) -> List[models.Measurement]:
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
