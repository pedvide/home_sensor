from sqlalchemy import ForeignKey, Column, text
from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from .database import Base

from typing import List


class Magnitude(Base):
    __tablename__ = "magnitudes"
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    name = Column(String, index=True, nullable=False)
    unit = Column(String, nullable=False)
    precision = Column(Float, nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))

    sensor = relationship("Sensor", back_populates="magnitudes")
    measurements = relationship("Measurement", back_populates="magnitude", lazy="dynamic")

    def __repr__(self):
        return (
            f"Magnitude(id: {self.id}, name={self.name}, "
            f"unit={self.unit}, sensor_id={self.sensor_id})"
        )


class StationSensor(Base):
    """Many to many relationship between sensors and stations"""

    __tablename__ = "stations_sensors"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    station_id = Column(Integer, ForeignKey("stations.id"))

    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    valid_until = Column(DateTime, nullable=True)

    sensor = relationship("Sensor", back_populates="stations_sensors_rel")
    station = relationship("Station", back_populates="stations_sensors_rel")

    def __init__(self, sensor=None, station=None):
        self.sensor = sensor
        self.station = station

    def __repr__(self):
        return (
            f"StationSensor(id={self.id}, "
            f"station_id={self.station_id}, sensor_id={self.sensor_id}, "
            f"created_at={self.created_at}, valid_until={self.valid_until})"
        )


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, unique=True, index=True, nullable=False)
    vendor = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))

    stations_sensors_rel = relationship("StationSensor", back_populates="sensor")
    _all_stations = association_proxy("stations_sensors_rel", "station")

    @property
    def stations(self):
        """Return valid stations"""
        return [
            station_sensor.station
            for station_sensor in self.stations_sensors_rel
            if station_sensor.valid_until is None
        ]

    magnitudes = relationship("Magnitude", back_populates="sensor",)
    measurements = relationship("Measurement", back_populates="sensor", lazy="dynamic")

    def __repr__(self):
        return f"Sensor(id={self.id}, name={self.name})"


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    token = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False)

    stations_sensors_rel = relationship("StationSensor", back_populates="station")
    _all_sensors = association_proxy("stations_sensors_rel", "sensor")

    def add_sensor(self, sensor: Sensor):
        self._all_sensors.append(sensor)

    def add_sensors(self, sensors: List[Sensor]):
        self._all_sensors.extend(sensors)

    @property
    def sensors(self):
        """Return valid sensors"""
        return [
            station_sensor.sensor
            for station_sensor in self.stations_sensors_rel
            if station_sensor.valid_until is None
        ]

    @sensors.setter
    def sensors(self, value):
        self.all_sensors = value

    measurements = relationship("Measurement", back_populates="station", lazy="dynamic")

    def __repr__(self):
        return f"Station(id={self.id}, token={self.token}, location={self.location})"


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(Integer, nullable=False, index=True)
    value = Column(String, nullable=False)

    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    station = relationship("Station", back_populates="measurements")
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    sensor = relationship("Sensor", back_populates="measurements")
    magnitude_id = Column(Integer, ForeignKey("magnitudes.id"), nullable=False)
    magnitude = relationship("Magnitude", back_populates="measurements")

    def __repr__(self):
        return f"Measurement(id={self.id}, timestamp={self.timestamp}, value={self.value})"


