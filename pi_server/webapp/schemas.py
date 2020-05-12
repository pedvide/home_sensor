from pydantic import BaseModel
from typing import List


## Schemas
class SensorBase(BaseModel):
    name: str

    magnitude_names: List[str]
    magnitude_units: List[str]


class SensorCreate(SensorBase):
    pass


class Sensor(SensorBase):
    id: int
    station_id: int

    class Config:
        orm_mode = True


class StationBase(BaseModel):
    token: str
    location: str


class StationCreate(StationBase):
    sensors: List[SensorCreate]


class Station(StationBase):
    id: int
    sensors: List[Sensor] = []

    class Config:
        orm_mode = True


class MeasurementBase(BaseModel):
    timestamp: int
    name: str
    unit: str
    value: str


class MeasurementCreate(MeasurementBase):
    pass


class Measurement(MeasurementBase):
    id: int
    station: Station
    sensor: Sensor

    class Config:
        orm_mode = True
