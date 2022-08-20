#pragma once

#include "common_sensor.h"
#include "logging.h"
#include <AM232X.h>
#include <ArduinoJson.h>
#include <Ticker.h>

class AMS2320Sensor : public Sensor {
public:
  AMS2320Sensor(const char *name, uint32_t period_s, size_t capacity,
                size_t response_capacity)
      : Sensor(name, period_s, capacity, response_capacity) {}

  bool setup() {
    log_println("Setting up AM2320 sensor...");
    if (!am2320.begin()) {
      delay(100);
      if (!am2320.isConnected()) {
        log_println("  AM2320 begin FAILED");
        return false;
      }
    }
    delay(500);

    log_printf("  Model: %d.\n"
               "  Version: %d.\n"
               "  Device ID: %d.\n"
               "  Done!\n",
               am2320.getModel(), am2320.getVersion(), am2320.getDeviceID());
    log_header_printf("AM2320 setup. model: %d, "
                      "version: %d, dev. id: %d.",
                      am2320.getModel(), am2320.getVersion(),
                      am2320.getDeviceID());

    return true;
  }

  void measure() {
    log_println("Measuring AM2320...");
    int conversion_ret_val;
    time_t now = UTC.now();
    float temperature, humidity;

    int status = am2320.read();
    if (status != AM232X_OK) {
      log_printf("  Error reading AM2320 (%d).\n", status);
      num_measurement_errors++;
      return;
    }

    // sensor
    humidity = am2320.getHumidity();
    temperature = am2320.getTemperature();

    SensorData humidity_data = {now, id, hum_id};
    conversion_ret_val = snprintf(
        humidity_data.value, sizeof(humidity_data.value), "%.3f", humidity);
    if (conversion_ret_val > 0) {
      log_printf("  Humidity: %.2f %%.\n", humidity);
      sensor_buffer.push(humidity_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    } else {
      log_printf("  Problem converting humidity (%.2f %%) to char[].\n",
                 humidity);
    }

    SensorData temperature_data = {now, id, temp_id};
    conversion_ret_val =
        snprintf(temperature_data.value, sizeof(temperature_data.value), "%.3f",
                 temperature);
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

  void setup_json(JsonObject &sensor_json) {
    sensor_json["name"] = name;
    JsonArray sensor_1_in_magnitudes =
        sensor_json.createNestedArray("magnitudes");

    JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
    mag1_in["name"] = "temperature";
    mag1_in["unit"] = "C";
    mag1_in["precision"] = 0.1;

    JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
    mag2_in["name"] = "humidity";
    mag2_in["unit"] = "%";
    mag2_in["precision"] = 0.1;
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
        "  am2320_sensor_id: %d, am2320_temp_id: %d, am2320_hum_id: %d.\n", id,
        temp_id, hum_id);
    log_header_printf(
        "  AM2320 sensor_id: %d, temperature_id: %d, humidity_id: %d.", id,
        temp_id, hum_id);

    return true;
  }

private:
  uint8_t temp_id, hum_id;
  AM232X am2320;
};

AMS2320Sensor am2320_sensor("AM2320", 10,
                            JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) +
                                2 * JSON_OBJECT_SIZE(3),
                            JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) +
                                2 * JSON_OBJECT_SIZE(4));
Ticker am2320_measurement_timer([]() { return am2320_sensor.measure(); },
                                am2320_sensor.period_s * 1e3, 0, MILLIS);
