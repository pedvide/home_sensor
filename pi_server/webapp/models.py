from sqlalchemy import Table, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


sensor_magnitude = Table(
    "sensor_magnitude",
    Base.metadata,
    Column("magnitude_id", Integer, ForeignKey("magnitudes.id"), primary_key=True),
    Column("sensors_id", Integer, ForeignKey("sensors.id"), primary_key=True),
)


class Magnitude(Base):
    __tablename__ = "magnitudes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    unit = Column(String, nullable=False)
    sensors = relationship(
        "Sensor", secondary=sensor_magnitude, back_populates="magnitudes", order_by="Sensor.id",
    )
    measurements = relationship(
        "Measurement",
        back_populates="magnitude",
        order_by="Measurement.timestamp",
        cascade="all, delete, delete-orphan",
    )


station_sensor = Table(
    "station_sensor",
    Base.metadata,
    Column("sensors_id", Integer, ForeignKey("sensors.id"), primary_key=True),
    Column("station_id", Integer, ForeignKey("stations.id"), primary_key=True),
)


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    magnitudes = relationship(
        "Magnitude", secondary=sensor_magnitude, back_populates="sensors", order_by=Magnitude.id
    )
    stations = relationship(
        "Station", secondary=station_sensor, back_populates="sensors", order_by="Station.id",
    )
    measurements = relationship(
        "Measurement",
        back_populates="sensor",
        order_by="Measurement.timestamp",
        cascade="all, delete, delete-orphan",
    )


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=False)
    sensors = relationship(
        "Sensor", secondary=station_sensor, back_populates="stations", order_by=Sensor.id
    )
    measurements = relationship(
        "Measurement",
        back_populates="station",
        order_by="Measurement.timestamp",
        cascade="all, delete, delete-orphan",
    )


class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    value = Column(String, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    station = relationship("Station", back_populates="measurements")
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    sensor = relationship("Sensor", back_populates="measurements")
    magnitude_id = Column(Integer, ForeignKey("magnitudes.id"), nullable=False)
    magnitude = relationship("Magnitude", back_populates="measurements")
