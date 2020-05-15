from typing import Dict

Session = dict


def init_db():
    stations: Dict[str, "Station"] = dict()
    measurements: Dict[str, "Measurement"] = dict()
    sensors: Dict[str, "Sensor"] = dict()
    magnitudes: Dict[str, "Magnitude"] = dict()
    db = {
        "stations": stations,
        "measurements": measurements,
        "sensors": sensors,
        "magnitudes": magnitudes,
    }
    return db


def clear_db():
    db["stations"] = dict()
    db["measurements"] = dict()
    db["sensors"] = dict()
    db["magnitudes"] = dict()


db = init_db()


def get_db():
    try:
        yield db
    finally:
        pass
