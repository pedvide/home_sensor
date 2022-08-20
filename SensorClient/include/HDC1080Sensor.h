#pragma once

#include "ClosedCube_HDC1080.h" // HDC1080 library
#include "common_sensor.h"
#include "logging.h"
#include <ArduinoJson.h>
#include <Ticker.h>

class HDC1080Sensor : public Sensor {
public:
  HDC1080Sensor(const char *name, uint32_t period_s, size_t capacity,
                size_t response_capacity)
      : Sensor(name, period_s, capacity, response_capacity){};

  void setup_json(JsonObject &sensor_json) {
    sensor_json["name"] = name;
    JsonArray sensor_1_in_magnitudes =
        sensor_json.createNestedArray("magnitudes");

    JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
    mag1_in["name"] = "temperature";
    mag1_in["unit"] = "C";
    mag1_in["precision"] = 0.2;

    JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
    mag2_in["name"] = "humidity";
    mag2_in["unit"] = "%";
    mag2_in["precision"] = 2;
  }

  bool parse_json(JsonObject &sensor_json_response) {
    id = sensor_json_response["id"];
    JsonArray magnitudes_json =
        sensor_json_response["magnitudes"].as<JsonArray>();
    for (JsonObject mag_json : magnitudes_json) {
      const char *name = mag_json["name"];
      if (strcmp(name, "temperature") == 0) {
        temp_id = mag_json["id"];
      } else if (strcmp(name, "humidity") == 0) {
        hum_id = mag_json["id"];
      }
    }
    log_printf(
        "  hdc1080_sensor_id: %d, hdc1080_temp_id: %d, hdc1080_hum_id: %d.\n",
        id, temp_id, hum_id);
    log_header_printf(
        "  HDC1080 sensor_id: %d, temperature_id: %d, humidity_id: %d.", id,
        temp_id, hum_id);

    return true;
  }

  bool setup() {
    log_printf("Setting up HDC1080 sensor...\n");

    // Enable HDC1080
    hdc1080.begin(0x40);
    hdc1080.setResolution(HDC1080_RESOLUTION_14BIT, HDC1080_RESOLUTION_14BIT);

    if (hdc1080.readManufacturerId() == 0xFFFF) {
      log_println("  Communication error!");
      return false;
    }

    // Print HDC1080 versions
    log_printf("  Manufacturer ID: 0x%X\n", hdc1080.readManufacturerId());
    log_printf("  Device ID: 0x%X\n", hdc1080.readDeviceId());
    HDC1080_SerialNumber sernum = hdc1080.readSerialNumber();
    log_printf("  Serial number: %02X-%04X-%04X.\n", sernum.serialFirst,
               sernum.serialMid, sernum.serialLast);

    delay(500);
    log_println("  Done!");
    log_header_printf("HDC1080 manufacturer ID v. 0x%X, dev ID: 0x%X, "
                      "serial no.: %02X-%04X-%04X.",
                      hdc1080.readManufacturerId(), hdc1080.readDeviceId(),
                      sernum.serialFirst, sernum.serialMid, sernum.serialLast);
    return true;
  }

  void measure() {
    log_println("Measuring HDC1080...");
    int conversion_ret_val;
    time_t now = UTC.now();
    float temperature, humidity;

    // sensor
    humidity = hdc1080.readHumidity();
    temperature = hdc1080.readTemperature();

    if (isnan(humidity)) {
      log_println("  Error reading humidity.");
      num_measurement_errors++;
    } else if (humidity > 99.99) {
      log_printf("  Error reading humidity (%.1f).\n", humidity);
      num_measurement_errors++;
    } else {
      SensorData humidity_data = {now, id, hum_id};
      conversion_ret_val = snprintf(
          humidity_data.value, sizeof(humidity_data.value), "%.1f", humidity);
      if (conversion_ret_val > 0) {
        log_printf("  Humidity: %.1f %%.\n", humidity);
        sensor_buffer.push(humidity_data);
        if (num_measurement_errors > 0) {
          num_measurement_errors--;
        }
      } else {
        log_printf("  Problem converting humidity (%.1f %%) to char[].\n",
                   humidity);
      }
    }

    if (isnan(temperature)) {
      log_println("  Error reading temperature.");
      num_measurement_errors++;
    } else if (temperature > 120) {
      log_printf("  Error reading temperature (%.2f).\n", temperature);
      num_measurement_errors++;
    } else {
      SensorData temperature_data = {now, id, temp_id};
      conversion_ret_val =
          snprintf(temperature_data.value, sizeof(temperature_data.value),
                   "%.2f", temperature);
      if (conversion_ret_val > 0) {
        log_printf("  Temperature: %.2f C.\n", temperature);
        sensor_buffer.push(temperature_data);
        if (num_measurement_errors > 0) {
          num_measurement_errors--;
        }
      } else {
        log_printf("  Problem converting temperature (%.2f C) to char[].\n",
                   temperature);
      }
    }
  }

  // HDC1080 Sensor
  uint8_t temp_id, hum_id;
  ClosedCube_HDC1080 hdc1080;
};

HDC1080Sensor hdc1080_sensor("HDC1080", 10,
                             JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) +
                                 2 * JSON_OBJECT_SIZE(3),
                             JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) +
                                 2 * JSON_OBJECT_SIZE(4));
Ticker hdc1080_measurement_timer([]() { return hdc1080_sensor.measure(); },
                                 hdc1080_sensor.period_s * 1e3, 0, MILLIS);
