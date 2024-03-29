from . import models, schemas
from .database import Session, InfluxDBClient, INFLUXDB_BUCKET
from typing import List, Optional
from datetime import datetime

from influxdb_client import Point

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


def get_sensor_by_name_and_tag(db: Session, name: str, tag: str = None) -> Optional[models.Sensor]:
    return (
        db.query(models.Sensor)
        .filter(
            models.Sensor.name == name,
            models.Sensor.tag.is_(None) if tag is None else (models.Sensor.tag == tag),
        )
        .one_or_none()
    )


def create_sensor(db: Session, sensor: schemas.SensorCreate) -> models.Sensor:
    db_sensor = models.Sensor(name=sensor.name, tag=sensor.tag)

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
    db_station = models.Station(
        location=station.location, token=station.token, hostname=station.hostname
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)

    for sensor in station.sensors:
        create_station_sensor(db, db_station, sensor)

    return db_station


def update_station(db: Session, db_station: models.Station, station: schemas.StationCreate):
    if db_station.hostname != station.hostname:
        db_station.hostname != station.hostname

    db.commit()
    return db_station


def get_station_sensors(
    db: Session, db_station: models.Station, offset: int = 0, limit: int = 10
) -> List[models.Sensor]:
    return db_station.sensors[offset:limit]


def get_station_sensor(
    db: Session, db_station: models.Station, db_sensor: models.Sensor
) -> models.Sensor:
    for sensor in db_station.sensors:
        if sensor.id == db_sensor.id:
            return sensor


def add_station_sensor(db: Session, db_station: models.Station, db_sensor: models.Sensor) -> None:
    db_station.add_sensor(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


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


def transform_measurement(db: Session, record_values: dict):
    """Enrich the influxdb measurement to adapt to schema"""
    return {
        **record_values,
        "value": record_values["_value"],
        "timestamp": int(record_values["_time"].timestamp()),
        "magnitude": get_magnitude(db, record_values["magnitude_id"]),
    }


def get_station_measurements(
    db: Session,
    db_influx: InfluxDBClient,
    station_id: int,
    offset: int = 0,
    limit: int = 10,
):
    query_api = db_influx.query_api()
    tables = query_api.query(
        f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -15d)
    |> filter(
        fn:(r) => r._measurement == "raw_data" and
                  r.station_id == "{station_id}"
       )
    |> sort(desc: true)
    |> limit(n: {limit}, offset: {offset})
    """
    )

    measurements = [
        transform_measurement(db, record.values) for table in tables for record in table
    ]
    return measurements


# Measurements
def get_all_measurements(
    db: Session,
    db_influx: InfluxDBClient,
    order: str = "timestamp",
    offset: int = 0,
    limit: int = 10,
):
    query_api = db_influx.query_api()
    tables = query_api.query(
        f"""
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: 0)
    |> filter(fn:(r) => r._measurement == "raw_data")
    |> sort(desc: true)
    |> limit(n: {limit}, offset: {offset})
    """
    )

    measurements = [
        transform_measurement(db, record.values) for table in tables for record in table
    ]
    return measurements


def create_measurements(
    db: Session,
    db_influx: InfluxDBClient,
    station_id: int,
    measurements: List[schemas.MeasurementCreate],
):
    """Create measurements and send it to influxdb"""
    point_measurements = []
    response_measurements = []

    for measurement in measurements:
        time = measurement.timestamp
        value = float(measurement.value)
        station = get_station(db, station_id)

        magnitude_id = str(measurement.magnitude_id)
        magnitude = get_magnitude(db, magnitude_id)

        sensor_id = str(measurement.sensor_id)
        sensor = get_sensor(db, sensor_id)

        point_measurement = (
            Point("raw_data")
            .time(time, write_precision="s")
            .tag("station_id", station_id)
            .tag("station_location", station.location)
            .tag("station_token", station.token)
            .tag("magnitude_id", magnitude_id)
            .tag("magnitude_name", magnitude.name)
            .tag("sensor_id", sensor_id)
            .tag("sensor_name", sensor.name)
            .field("value", value)
        )
        point_measurements.append(point_measurement)
        response_measurements.append(
            dict(
                station_id=station_id,
                **measurement.dict(),
                magnitude=get_magnitude(db, measurement.magnitude_id),
            )
        )

    try:
        with db_influx.write_api() as write_api:
            write_api.write(bucket=INFLUXDB_BUCKET, record=point_measurements)
    except Exception as e:
        raise InfluxDBError("Error writing a measurement") from e
    else:
        return response_measurements
