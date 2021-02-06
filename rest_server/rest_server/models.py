from sqlalchemy import ForeignKey, Column, text
from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

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

    magnitudes = relationship("Magnitude", back_populates="sensor")

    def __repr__(self):
        return f"Sensor(id={self.id}, name={self.name})"


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)"))
    token = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False)
    hostname = Column(String, nullable=False, unique=True)

    stations_sensors_rel = relationship("StationSensor", back_populates="station")
    _all_sensors = association_proxy("stations_sensors_rel", "sensor")

    def add_sensor(self, sensor: Sensor):
        self._all_sensors.append(sensor)

    @property
    def sensors(self):
        """Return valid sensors"""
        return [
            station_sensor.sensor
            for station_sensor in self.stations_sensors_rel
            if station_sensor.valid_until is None
        ]

    def __repr__(self):
        return f"Station(id={self.id}, token={self.token}, location={self.location})"


# class Measurement(Base):
#     __tablename__ = "measurements"

#     id = Column(Integer, primary_key=True, index=True)

#     timestamp = Column(Integer, nullable=False, index=True)
#     value = Column(String, nullable=False)

#     station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
#     sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
#     magnitude_id = Column(Integer, ForeignKey("magnitudes.id"), nullable=False)
#     magnitude = relationship("Magnitude")

#     def __repr__(self):
#         return f"Measurement(id={self.id}, timestamp={self.timestamp}, value={self.value})"


# Base.metadata.create_all(bind=engine)
# db = SessionLocal()
# m = Magnitude(name="temp", unit="C", precision="2")
# db.add(m)
# db.commit()
# db.refresh(m)
# db.query(Magnitude).all()

# s = Sensor(name="AM")
# db.add(s)
# db.commit()
# db.refresh(s)
# db.query(Sensor).all()

# s.magnitudes.append(m)
# db.commit()
# s.magnitudes

# st = Station(token="asdasdas", location="32vfwf")
# db.add(st)
# db.commit()
# db.refresh(st)
# db.query(Station).all()

# st_s = StationSensor(sensor=s, station=st)
# db.add(st_s)
# db.commit()
# db.refresh(st_s)
# db.query(StationSensor).all()
# from datetime import datetime
# (
#     db.query(Sensor)
#     .filter(Sensor.stations_sensors_rel.any(StationSensor.created_at > datetime(2020, 6, 10)))
#     .all()
# )
# (
#     db.query(Sensor)
#     .filter(Sensor.stations_sensors_rel.any(StationSensor.valid_until.is_(None)))
#     .all()
# )
# (
#     db.query(Sensor)
#     .filter(Sensor.stations_sensors_rel.any(StationSensor.valid_until < datetime(2020, 6, 10)))
#     .all()
# )

# s2 = Sensor(name="DFBSEDF")
# db.add(s2)
# db.commit()
# st2 = Station(token="sdge34tg", location="hsdv")
# db.add(st2)
# db.commit()

# st2.sensors.add_sensor(s2)
# db.commit()
# db.query(StationSensor).all()
# (
#     db.query(Sensor)
#     .filter(Sensor.stations_sensors_rel.any(StationSensor.station == st))
#     .all()
# )

# st2.sensors.add_sensor(s)
# db.commit()
# db.query(StationSensor).all()
# (
#     db.query(StationSensor)
#     .filter(StationSensor.sensor == s2, StationSensor.station == st2)
#     .one().valid_until
# ) = datetime.now()
