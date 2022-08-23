#pragma once

#include "ccs811.h" // CCS811 library
#include "common_sensor.h"
#include "logging.h"
#include <ArduinoJson.h>
#include <Ticker.h>

class CCS811Sensor : public Sensor {
public:
  CCS811Sensor(const char *name, uint32_t period_s, size_t capacity,
               size_t response_capacity)
      : Sensor(name, period_s, capacity, response_capacity){};

  void setup_json(JsonObject &sensor_json) {
    sensor_json["name"] = name;
    JsonArray sensor_1_in_magnitudes =
        sensor_json.createNestedArray("magnitudes");

    JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
    mag1_in["name"] = "eco2";
    mag1_in["unit"] = "ppm";
    mag1_in["precision"] = 1;

    JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
    mag2_in["name"] = "etvoc";
    mag2_in["unit"] = "ppb";
    mag2_in["precision"] = 1;
  }

  bool parse_json(JsonObject &sensor_json_response) {
    id = sensor_json_response["id"];
    JsonArray magnitudes_json =
        sensor_json_response["magnitudes"].as<JsonArray>();
    for (JsonObject mag_json : magnitudes_json) {
      const char *name = mag_json["name"];
      if (strcmp(name, "eco2") == 0) {
        eco2_id = mag_json["id"];
      } else if (strcmp(name, "etvoc") == 0) {
        etvoc_id = mag_json["id"];
      }
    }
    log_printf(
        "  ccs811_sensor_id: %d, ccs811_eco2_id: %d, ccs811_etvoc_id: %d.\n",
        id, eco2_id, etvoc_id);
    log_header_printf("  CCS811 sensor_id: %d, eCO2_id: %d, eTVOC_id: %d.", id,
                      eco2_id, etvoc_id);

    return true;
  }

  bool setup() {
    log_printf("Setting up CCS811 sensor (version %d)...\n", CCS811_VERSION);

    // Enable CCS811
    ccs811.set_i2cdelay(20); // Needed for ESP8266 because it doesn't handle I2C
                             // clock stretch correctly
    bool ok = ccs811.begin();
    if (!ok) {
      log_println("  CCS811 begin FAILED");
      return false;
    }

    // Print CCS811 versions
    log_printf("  hardware version: %X\n", ccs811.hardware_version());
    log_printf("  bootloader version: %X\n", ccs811.bootloader_version());
    log_printf("  application version: %X\n", ccs811.application_version());

    // Start measuring
    ok = ccs811.start(CCS811_MODE_10SEC);
    if (!ok) {
      log_println("  CCS811 start FAILED");
      return false;
    }

    delay(500);
    log_println("  Done!");
    log_header_printf("CCS811 setup. lib v. %d, hw v.: 0x%X, "
                      "bootldr v.: 0x%X, app v.: 0x%X.",
                      CCS811_VERSION, ccs811.hardware_version(),
                      ccs811.bootloader_version(),
                      ccs811.application_version());
    return true;
  }

  void measure() {
    log_println("Measuring CCS811...");
    int conversion_ret_val;
    time_t now = UTC.now();

    // sensor
    uint16_t eco2, etvoc, errstat, raw;
    ccs811.read(&eco2, &etvoc, &errstat, &raw);

    // Check for errors
    if (errstat != CCS811_ERRSTAT_OK) {
      num_measurement_errors++;
      if (errstat == CCS811_ERRSTAT_OK_NODATA) {
        log_println("  error: waiting for (new) data");
      } else if (errstat & CCS811_ERRSTAT_I2CFAIL) {
        log_println("  I2C error");
      } else {
        log_printf("  other error: errstat (%X) =", errstat);
        log_println(ccs811.errstat_str(errstat));
      }
      return;
    }

    SensorData eco2_data = {now, id, eco2_id};
    conversion_ret_val =
        snprintf(eco2_data.value, sizeof(eco2_data.value), "%d", eco2);
    if (conversion_ret_val > 0) {
      log_printf("  equivalent CO2: %d ppm.\n", eco2);
      sensor_buffer.push(eco2_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    } else {
      log_printf("  Problem converting equivalent CO2 (%d ppm) to char[].\n",
                 eco2);
    }

    SensorData etvoc_data = {now, id, etvoc_id};
    conversion_ret_val =
        snprintf(etvoc_data.value, sizeof(etvoc_data.value), "%d", etvoc);
    if (conversion_ret_val > 0) {
      log_printf("  total VOC: %d ppb.\n", etvoc);
      sensor_buffer.push(etvoc_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    } else {
      log_printf("  Problem converting total VOC (%d ppb) to char[].\n", etvoc);
    }
  }

  void correct_ccs811_envdata(float humidity, float temperature) {
    ccs811.set_envdata(((uint16_t)humidity + 250) / 500,
                       ((uint16_t)temperature + 25250) / 500);
  }

  // CCS811 Sensor
  uint8_t eco2_id, etvoc_id;
  CCS811 ccs811;
};

CCS811Sensor ccs811_sensor("CCS811", 10,
                           JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) +
                               2 * JSON_OBJECT_SIZE(3),
                           JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) +
                               2 * JSON_OBJECT_SIZE(4));
Ticker ccs811_measurement_timer([]() { return ccs811_sensor.measure(); },
                                ccs811_sensor.period_s * 1e3, 0, MILLIS);
