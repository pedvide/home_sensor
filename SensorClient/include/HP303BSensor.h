#pragma once

#include "LOLIN_HP303B.h" // HP303B library
#include "common_sensor.h"
#include "logging.h"
#include <ArduinoJson.h>
#include <Ticker.h>

// HP303B Sensor
uint8_t hp303b_sensor_id, hp303b_temp_id, hp303b_pres_id;
const char *sensor_hp303b_name PROGMEM = "HP303B";
LOLIN_HP303B hp303b;
const uint32_t hp303b_period_s = 10;
const size_t capacity_hp303b =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 2 * JSON_OBJECT_SIZE(3);
const size_t response_capacity_hp303b =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 2 * JSON_OBJECT_SIZE(4);

void setup_hp303b_sensor_json(JsonObject &sensor_json) {
  sensor_json["name"] = sensor_hp303b_name;
  JsonArray sensor_1_in_magnitudes =
      sensor_json.createNestedArray("magnitudes");

  JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
  mag1_in["name"] = "temperature";
  mag1_in["unit"] = "C";
  mag1_in["precision"] = 0.5;

  JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
  mag2_in["name"] = "pressure";
  mag2_in["unit"] = "Pa";
  mag2_in["precision"] = 10;
}

bool parse_hp303b_sensor_json(JsonObject &sensor_json_response) {
  hp303b_sensor_id = sensor_json_response["id"];
  JsonArray magnitudes_json =
      sensor_json_response["magnitudes"].as<JsonArray>();
  for (JsonObject mag_json : magnitudes_json) {
    const char *name = mag_json["name"];
    if (strcmp(name, "temperature") == 0) {
      hp303b_temp_id = mag_json["id"];
    } else if (strcmp(name, "pressure") == 0) {
      hp303b_pres_id = mag_json["id"];
    }
  }
  log_printf(
      "  hp303b_sensor_id: %d, hp303b_temp_id: %d, hp303b_pres_id: %d.\n",
      hp303b_sensor_id, hp303b_temp_id, hp303b_pres_id);
  log_header_printf(
      "  HP303B sensor_id: %d, temperature_id: %d, pressure_id: %d.",
      hp303b_sensor_id, hp303b_temp_id, hp303b_pres_id);

  return true;
}

bool setup_hp303b_sensor() {
  log_println("Setting up HP303B sensor...");
  hp303b.begin();
  delay(500);

  log_printf("  Product ID: %d.\n"
             "  Revision ID: %d.\n"
             "  Done!\n",
             hp303b.getProductId(), hp303b.getRevisionId());
  log_header_printf("HP303B setup. product ID: %d, "
                    "revision ID: %d.",
                    hp303b.getProductId(), hp303b.getRevisionId());

  return true;
}

void measure_hp303b_sensor() {
  log_println("Measuring HP303B...");
  const uint8_t oversampling = 7;
  int conversion_ret_val;
  time_t now = UTC.now();
  int temperature, pressure;
  int status;

  status = hp303b.measureTempOnce(temperature, oversampling);
  switch (status) {
  case HP303B__SUCCEEDED:
    break;
  case HP303B__FAIL_UNKNOWN:
    log_println("  Unknown error reading HP303B.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_INIT_FAILED:
    log_println("  Initialization error reading HP303B.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_TOOBUSY:
    log_println("  Error: HP303B is busy.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_UNFINISHED:
    log_println("  Error: HP303B could not finish the measurement on time.");
    num_measurement_errors++;
    break;
  }
  SensorData temperature_data = {now, hp303b_sensor_id, hp303b_temp_id};
  conversion_ret_val =
      snprintf(temperature_data.value, sizeof(temperature_data.value), "%d",
               temperature);
  if (conversion_ret_val > 0) {
    log_printf("  Temperature: %d C.\n", temperature);
    sensor_buffer.push(temperature_data);
    if (num_measurement_errors > 0) {
      num_measurement_errors--;
    }
  } else {
    log_printf("  Problem converting temperature (%d C) to char[].\n",
               temperature);
  }

  status = hp303b.measurePressureOnce(pressure, oversampling);
  switch (status) {
  case HP303B__SUCCEEDED:
    break;
  case HP303B__FAIL_UNKNOWN:
    log_println("  Unknown error reading HP303B.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_INIT_FAILED:
    log_println("  Initialization error reading HP303B.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_TOOBUSY:
    log_println("  Error: HP303B is busy.");
    num_measurement_errors++;
    break;
  case HP303B__FAIL_UNFINISHED:
    log_println("  Error: HP303B could not finish the measurement on time.");
    num_measurement_errors++;
    break;
  }
  SensorData pressure_data = {now, hp303b_sensor_id, hp303b_pres_id};
  conversion_ret_val = snprintf(pressure_data.value,
                                sizeof(pressure_data.value), "%d", pressure);
  if (conversion_ret_val > 0) {
    log_printf("  Pressure: %d hPa.\n", pressure / 100);
    sensor_buffer.push(pressure_data);
    if (num_measurement_errors > 0) {
      num_measurement_errors--;
    }
  } else {
    log_printf("  Problem converting pressure (%d hPa) to char[].\n",
               pressure / 100);
  }
}

Ticker hp303b_measurement_timer(measure_hp303b_sensor, hp303b_period_s * 1e3, 0,
                                MILLIS);
