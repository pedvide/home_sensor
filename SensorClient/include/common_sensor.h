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
  Sensor(const char *name, uint32_t period_s, size_t capacity,
         size_t response_capacity)
      : name{name}, period_s{period_s}, capacity{capacity},
        response_capacity{response_capacity} {};

  virtual bool setup() = 0;
  virtual void measure() = 0;
  virtual void watchdog(){};
  virtual void setup_json(JsonObject &sensor_json) = 0;
  virtual bool parse_json(JsonObject &sensor_json_response) = 0;

  uint8_t id;
  const char *name;
  const uint32_t period_s;
  const size_t capacity;
  const size_t response_capacity;
};
