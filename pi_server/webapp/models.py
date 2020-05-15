from dataclasses import dataclass
from typing import List


@dataclass
class Magnitude:
    id: int
    name: str
    unit: str


@dataclass
class Sensor:
    name: str
    magnitude_ids: List[int]
    id: int


@dataclass
class Station:
    token: str
    location: str
    id: int
    sensor_ids: List[int]


@dataclass
class Measurement:
    id: int
    station_id: int
    sensor_id: int
    magnitude_id: int
    timestamp: int
    value: str
