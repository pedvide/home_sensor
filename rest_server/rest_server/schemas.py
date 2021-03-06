from pydantic import BaseModel, Field
from typing import List


class MagnitudeBase(BaseModel):
    name: str
    unit: str
    precision: float


class MagnitudeCreate(MagnitudeBase):
    pass


class Magnitude(MagnitudeBase):
    id: int

    class Config:
        orm_mode = True


class SensorBase(BaseModel):
    name: str
    tag: str = None


class SensorCreate(SensorBase):
    magnitudes: List[MagnitudeCreate]


class Sensor(SensorBase):
    id: int
    magnitudes: List[Magnitude]

    class Config:
        orm_mode = True


class StationBase(BaseModel):
    token: str
    location: str
    hostname: str


class StationCreate(StationBase):
    sensors: List[SensorCreate] = []


class Station(StationBase):
    id: int
    sensors: List[Sensor] = []

    class Config:
        orm_mode = True


class MeasurementBase(BaseModel):
    timestamp: int
    value: str


class MeasurementCreate(MeasurementBase):
    magnitude_id: int
    sensor_id: int


class Measurement(MeasurementBase):
    # id: int
    time: int = Field(alias="timestamp")
    station_id: int
    sensor_id: int
    magnitude: Magnitude

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
