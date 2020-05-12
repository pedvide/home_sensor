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


class SingleMeasurementBase(BaseModel):
    name: str
    unit: str
    value: str


class SingleMeasurementCreate(SingleMeasurementBase):
    pass


class SingleMeasurement(SingleMeasurementBase):
    id: int
    station_id: int
    sensor_id: int
    timestamp: int

    class Config:
        orm_mode = True


class MeasurementBase(BaseModel):
    timestamp: int


class MeasurementCreate(MeasurementBase):
    data: List[SingleMeasurementCreate]


class Measurement(MeasurementBase):
    data: List[SingleMeasurement]
