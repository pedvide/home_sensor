from typing import Dict

Session = dict


def get_db():
    try:
        db = init_db()
        yield db
    finally:
        clear_db(db)


def init_db():
    stations: Dict[str, "Station"] = dict()
    measurements: Dict[str, "Measurement"] = dict()
    sensors: Dict[str, "Sensor"] = dict()
    db = {"stations": stations, "measurements": measurements, "sensors": sensors}
    return db


def clear_db(db):
    db["stations"] = dict()
    db["measurements"] = dict()
    db["sensors"] = dict()
