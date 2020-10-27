from . import models, schemas
from .database import Session, InfluxDBClient
from typing import List, Optional
from datetime import datetime

# from pprint import pprint


class InfluxDBError(Exception):
    pass


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


def create_station(db: Session, station: schemas.StationCreate) -> models.Station:
    db_station = models.Station(location=station.location, token=station.token)
    db.add(db_station)
    db.commit()
    db.refresh(db_station)

    for sensor in station.sensors:
        create_station_sensor(db, db_station, sensor)

    return db_station


def get_station_sensors(
    db: Session, db_station: models.Station, offset: int = 0, limit: int = 10
) -> List[models.Sensor]:
    return db_station.sensors[offset:limit]


def get_station_sensor(
    db: Session, db_station: models.Station, db_sensor: models.Sensor
) -> models.Sensor:
    return [sensor for sensor in db_station.sensors if sensor.id == db_sensor.id][0]


def add_station_sensor(db: Session, db_station: models.Station, db_sensor: models.Sensor) -> None:
    db_station.add_sensor(db_sensor)
    db.commit()


def create_station_sensor(
    db: Session, db_station: models.Station, sensor: schemas.SensorCreate
) -> models.Sensor:
    db_sensor = create_sensor(db, sensor)
    add_station_sensor(db, db_station, db_sensor)

    db.commit()
    db.refresh(db_sensor)
    return db_sensor


def delete_station_sensor(
    db: Session, db_station: models.Station, db_sensor: models.Sensor
) -> None:
    db_station_sensor = (
        db.query(models.StationSensor)
        .filter(
            models.StationSensor.station == db_station, models.StationSensor.sensor == db_sensor
        )
        .filter(models.StationSensor.valid_until.is_(None))
        .one()
    )
    db_station_sensor.valid_until = datetime.now()
    db.commit()


def transform_measurement(db: Session, db_measurement: dict):
    """Enrich the influxdb measurement to adapt to schema"""
    return {
        **db_measurement,
        "timestamp": db_measurement["time"],
        "magnitude": get_magnitude(db, db_measurement["magnitude_id"]),
    }


def get_station_measurements(
    db: Session, db_influx: InfluxDBClient, station_id: int, offset: int = 0, limit: int = 10,
):
    db_measurements = db_influx.query(
        f"SELECT * FROM raw_data WHERE station_id='{station_id}' "
        f"ORDER BY time DESC LIMIT {limit} OFFSET {offset}",
        epoch="s",
    ).get_points()

    measurements = [transform_measurement(db, db_measurement) for db_measurement in db_measurements]
    return measurements


# Measurements
def get_all_measurements(
    db: Session,
    db_influx: InfluxDBClient,
    order: str = "timestamp",
    offset: int = 0,
    limit: int = 10,
):
    db_measurements = db_influx.query(
        f"SELECT * FROM raw_data ORDER BY time DESC LIMIT {limit} OFFSET {offset}", epoch="s",
    ).get_points()

    measurements = [transform_measurement(db, db_measurement) for db_measurement in db_measurements]
    return measurements


def create_measurements(
    db: Session,
    db_influx: InfluxDBClient,
    station_id: int,
    measurements: List[schemas.MeasurementCreate],
):
    """Create measurements and send it to influxdb"""
    json_measurements = []
    response_measurements = []

    for measurement in measurements:
        time = measurement.timestamp
        value = float(measurement.value)
        station = get_station(db, station_id)

        magnitude_id = str(measurement.magnitude_id)
        magnitude = get_magnitude(db, magnitude_id)

        sensor_id = str(measurement.sensor_id)
        sensor = get_sensor(db, sensor_id)

        json_measurement = {
            "measurement": "raw_data",
            "time": time,
            "fields": {"value": value},
            "tags": dict(
                station_id=station_id,
                station_location=station.location,
                magnitude_id=magnitude_id,
                magnitude_name=magnitude.name,
                sensor_id=sensor_id,
                sensor_name=sensor.name,
            ),
        }
        json_measurements.append(json_measurement)
        response_measurements.append(
            dict(
                station_id=station_id,
                **measurement.dict(),
                magnitude=get_magnitude(db, measurement.magnitude_id),
            )
        )

    if db_influx.write_points(json_measurements, time_precision="s",):
        return response_measurements
    else:
        raise InfluxDBError("Error writing a measurement")
