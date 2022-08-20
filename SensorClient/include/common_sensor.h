#pragma once

#include "Arduino.h"
#include <ArduinoJson.h>
#include <CircularBuffer.h>

///// Common sensor
typedef struct {
  time_t epoch;
  uint8_t sensor_id;
  uint8_t magnitude_id;
  char value[10];
} SensorData;
SensorData sensor_data;
CircularBuffer<SensorData, 255> sensor_buffer; // Keep some raw data
uint8 num_measurement_errors = 0;

class Sensor {
public:
  Sensor(){};

  virtual bool setup() = 0;
  virtual void measure() = 0;
  virtual void setup_json(JsonObject &sensor_json) = 0;
  virtual bool parse_json(JsonObject &sensor_json_response) = 0;
};
