from typing import Dict

Session = dict

db = dict()


def init_db():
    global db
    stations: Dict[str, "Station"] = dict()
    measurements: Dict[str, "Measurement"] = dict()
    sensors: Dict[str, "Sensor"] = dict()
    db = {"stations": stations, "measurements": measurements, "sensors": sensors}
    return db


def clear_db():
    global db
    db["stations"] = dict()
    db["measurements"] = dict()
    db["sensors"] = dict()
