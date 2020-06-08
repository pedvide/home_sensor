from sqlalchemy import ForeignKey, Column, text
from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from .database import Base


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


class StationSensor(Base):
    """Many to many relationship between sensors and stations"""

    __tablename__ = "stations_sensors"
    sensor_id = Column(Integer, ForeignKey("sensors.id"), primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.row_id"), primary_key=True)


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    vendor = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    magnitudes = relationship("Magnitude", back_populates="sensor")
    stations = relationship("Station", secondary="stations_sensors", back_populates="sensors")
    measurements = relationship("Measurement", back_populates="sensor", lazy="dynamic")


class Station(Base):
    __tablename__ = "stations"
    row_id = Column(Integer, primary_key=True, index=True)
    id = Column(
        Integer,
        index=True,
        unique=False,
        nullable=False,
        default=text("(SELECT COALESCE(MAX(id), 0) + 1 FROM stations)"),
    )
    # period of time this row was valid, valid_until=null means is valid now
    valid_from = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    valid_until = Column(DateTime, nullable=True)
    # data
    token = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    sensors = relationship("Sensor", secondary="stations_sensors", back_populates="stations")
    measurements = relationship("Measurement", back_populates="station", lazy="dynamic")


class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    value = Column(String, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.row_id"), nullable=False)
    station = relationship("Station", back_populates="measurements")
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    sensor = relationship("Sensor", back_populates="measurements")
    magnitude_id = Column(Integer, ForeignKey("magnitudes.id"), nullable=False)
    magnitude = relationship("Magnitude", back_populates="measurements")
