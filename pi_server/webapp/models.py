from dataclasses import dataclass
from typing import List


@dataclass
class Sensor:
    name: str
    magnitude_names: List[str]
    magnitude_units: List[str]
    id: int
    station_id: int


@dataclass
class Station:
    token: str
    location: str
    id: int
    sensors: List[Sensor]


@dataclass
class Measurement:
    id: int
    station: Station
    sensor: Sensor
    timestamp: int
    name: str
    unit: str
    value: str
