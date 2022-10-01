#pragma once

#include "common_sensor.h"
#include "logging.h"
#include <ArduinoJson.h>
#include <Ticker.h>

class P1Sensor : public Sensor {
public:
  P1Sensor(const char *name, uint32_t period_s, size_t capacity,
           size_t response_capacity)
      : Sensor(name, period_s, capacity, response_capacity) {}

  bool setup() {
    log_println("Setting up P1 sensor...");
    // Setup a hw serial connection for communication with the P1 meter and
    // logging (not using inversion)
    Serial.begin(baud_rate, SERIAL_8N1, SERIAL_FULL);
    Serial.println("");
    Serial.flush();

    // Invert the RX serial port by setting a register value, this way the TX
    // might continue normally allowing the serial monitor to read println's
    USC0(UART0) = USC0(UART0) | BIT(UCRXI);

    log_printf("  Done!\n");
    log_header_printf("P1 setup.");

    return true;
  }

  void measure() {
    while (Serial.available()) {
      ESP.wdtDisable();
      telegram = Serial.readStringUntil('\n');
      telegram += "\n";
      ESP.wdtEnable(1);

      process_line(telegram);
      yield();
    }

    if (first_measurement &&
        (abs(defaultTZ->now() - getDatetime(p1_data.local_timestamp))) >
            max_time_no_measurent_s) {
      log_println(F("Too long without a valid measurement!"));
      ESP.restart();
    }
  }

  void setup_json(JsonObject &sensor_json) {
    sensor_json["name"] = name;
    JsonArray sensor_1_in_magnitudes =
        sensor_json.createNestedArray("magnitudes");

    JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
    mag1_in["name"] = "power_consumption_1";
    mag1_in["unit"] = "kWh";
    mag1_in["precision"] = 0.001;

    JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
    mag2_in["name"] = "power_consumption_2";
    mag2_in["unit"] = "kWh";
    mag2_in["precision"] = 0.001;

    JsonObject mag3_in = sensor_1_in_magnitudes.createNestedObject();
    mag3_in["name"] = "power_delivery_1";
    mag3_in["unit"] = "kWh";
    mag3_in["precision"] = 0.001;

    JsonObject mag4_in = sensor_1_in_magnitudes.createNestedObject();
    mag4_in["name"] = "power_delivery_2";
    mag4_in["unit"] = "kWh";
    mag4_in["precision"] = 0.001;

    JsonObject mag5_in = sensor_1_in_magnitudes.createNestedObject();
    mag5_in["name"] = "gas_consumption";
    mag5_in["unit"] = "m3";
    mag5_in["precision"] = 0.001;
  }

  bool parse_json(JsonObject &sensor_json_response) {
    id = sensor_json_response["id"];
    JsonArray magnitudes_json =
        sensor_json_response["magnitudes"].as<JsonArray>();

    for (JsonObject mag_json : magnitudes_json) {
      const char *name = mag_json["name"];
      if (strcmp(name, "power_consumption_1") == 0) {
        power_consumption_1_id = mag_json["id"];
      } else if (strcmp(name, "power_consumption_2") == 0) {
        power_consumption_2_id = mag_json["id"];
      } else if (strcmp(name, "power_delivery_1") == 0) {
        power_delivery_1_id = mag_json["id"];
      } else if (strcmp(name, "power_delivery_2") == 0) {
        power_delivery_2_id = mag_json["id"];
      } else if (strcmp(name, "gas_consumption") == 0) {
        gas_consumption_id = mag_json["id"];
      }
    }

    log_printf("  p1_sensor_id: %d, consumption ids: (%d, %d), delivery ids: "
               "(%d, %d), gas id: %d.\n",
               id, power_consumption_1_id, power_consumption_2_id,
               power_delivery_1_id, power_delivery_2_id, gas_consumption_id);
    log_header_printf(
        "  P1 sensor_id: %d, consumption ids: (%d, %d), delivery ids: "
        "(%d, %d), gas id: %d.\n",
        id, power_consumption_1_id, power_consumption_2_id, power_delivery_1_id,
        power_delivery_2_id, gas_consumption_id);

    return true;
  }

private:
  uint8_t power_consumption_1_id, power_consumption_2_id, power_delivery_1_id,
      power_delivery_2_id, gas_consumption_id;
  const uint32_t baud_rate = 115200;
  // Set during CRC checking
  uint32_t currentCRC = 0;

  const uint32_t max_time_no_measurent_s = 120;
  bool first_measurement = false;

  String telegram;

  // Data
  typedef struct {
    String local_timestamp;

    uint32_t consumption_1, consumption_2;
    uint32_t delivery_1, delivery_2;

    uint8_t actual_tariff;

    uint32_t actual_consumption, actual_delivery;

    uint32_t l1_instant_current;
    uint32_t l1_instant_power_consumption, l1_instant_power_delivery;

    String gas_local_timestamp;
    double gas_consumption;
  } P1Data;
  P1Data p1_data;

  unsigned int CRC16(unsigned int crc, unsigned char *buf, int len) {
    for (int pos = 0; pos < len; pos++) {
      crc ^= (unsigned int)buf[pos]; // * XOR byte into least sig. byte of crc
      // * Loop over each bit
      for (int i = 8; i != 0; i--) {
        // * If the LSB is set
        if ((crc & 0x0001) != 0) {
          // * Shift right and XOR 0xA001
          crc >>= 1;
          crc ^= 0xA001;
        }
        // * Else LSB is not set
        else {
          // * Just shift right
          crc >>= 1;
        }
      }
    }
    return crc;
  }

  double getValue(String buffer, char startchar, char endchar) {
    int startIdx = buffer.indexOf(startchar);
    int endIdx = buffer.lastIndexOf(endchar);

    String value = buffer.substring(startIdx + 1, endIdx);
    // log_println(value);
    int startNumber = 0;
    // remove leading zeros before converting to double
    for (uint32_t i = 0; i < value.length(); i++) {
      if (value[i] != '0') {
        if (value[i] == '.') {
          startNumber = i - 1;
        } else {
          startNumber = i;
        }
        break;
      }
    }
    String trimmed_value = value.substring(startNumber);
    // log_println(trimmed_value);
    return trimmed_value.toDouble();
  }

  String getText(String buffer, char startchar, char endchar) {
    int startIdx = buffer.indexOf(startchar);
    int endIdx = buffer.lastIndexOf(endchar);
    return buffer.substring(startIdx + 1, endIdx);
  }

  time_t getDatetime(String dsmr_timestamp) {
    return makeTime(dsmr_timestamp.substring(6, 8).toInt(),
                    dsmr_timestamp.substring(8, 10).toInt(),
                    dsmr_timestamp.substring(10, 12).toInt(),
                    dsmr_timestamp.substring(4, 6).toInt(),
                    dsmr_timestamp.substring(2, 4).toInt(),
                    2000 + dsmr_timestamp.substring(0, 2).toInt());
  }

  void process_line(String telegram) {
    bool result = decode_telegram(telegram);
    if (result) {
      print_data();
      queue_data();

      // record first measurement
      if (!first_measurement) {
        first_measurement = true;
      }
    }
  }

  // parsing of telegram according to Dutch ESMR 4.0 implementation
  // https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_32ffe3cc38.pdf
  bool decode_telegram(String telegram) {
    bool msgStart = telegram.startsWith("/");
    bool msgEnd = telegram.startsWith("!");
    bool validCRCFound = false;

    // log_println(telegram);
    // Serial.print(telegram);

    if (msgStart) {
      // Start found. Reset CRC calculation
      currentCRC =
          CRC16(0x0000, (unsigned char *)telegram.c_str(), telegram.length());
    } else if (msgEnd) {
      // End found, add to crc calc
      currentCRC = CRC16(currentCRC, (unsigned char *)telegram.c_str(), 1);

      char messageCRC[5];
      strncpy(messageCRC, telegram.c_str() + 1, 4);

      messageCRC[4] = 0; // * Thanks to HarmOtten (issue 5)
      validCRCFound = ((unsigned)strtol(messageCRC, NULL, 16) == currentCRC);

      if (validCRCFound) {
        log_println(F("Valid P1 data found!"));
      } else {
        log_println(F("Invalid P1 data found!"));
      }

      currentCRC = 0;
    } else {
      // Middle of message
      currentCRC = CRC16(currentCRC, (unsigned char *)telegram.c_str(),
                         telegram.length());
    }

    // 0-0:1.0.0(220821195452S)
    // 0-0:1.0.0 = Date-time stamp of the P1 message
    if (telegram.startsWith("0-0:1.0.0")) {
      p1_data.local_timestamp = getText(telegram, '(', ')');
    }

    // 1-0:1.8.1(000992.992*kWh)
    // 1-0:1.8.1 = Meter Reading electricity delivered to client (Tariff 1) in
    // 0,001 kWh
    if (telegram.startsWith("1-0:1.8.1")) {
      p1_data.consumption_1 = 1000.0 * getValue(telegram, '(', '*');
    }

    // 1-0:2.8.1(000560.157*kWh)
    // 1-0:2.8.1 = Meter Reading electricity delivered by client (Tariff 1) in
    // 0,001 kWh
    if (telegram.startsWith("1-0:2.8.1")) {
      p1_data.delivery_1 = 1000.0 * getValue(telegram, '(', '*');
    }

    // 1-0:1.8.2(000992.992*kWh)
    // 1-0:1.8.2 = Meter Reading electricity delivered to client (Tariff 2) in
    // 0,001 kWh
    if (telegram.startsWith("1-0:1.8.2")) {
      p1_data.consumption_2 = 1000.0 * getValue(telegram, '(', '*');
    }

    // 1-0:2.8.2(000560.157*kWh)
    // 1-0:2.8.2 = Meter Reading electricity delivered by client (Tariff 2) in
    // 0,001 kWh
    if (telegram.startsWith("1-0:2.8.2")) {
      p1_data.delivery_2 = 1000.0 * getValue(telegram, '(', '*');
    }

    // 0-0:96.14.0(0001)
    // 0-0:96.14.0 = Current tariff (1 or 2)
    if (telegram.startsWith("0-0:96.14.0")) {
      p1_data.actual_tariff = getValue(telegram, '(', ')');
    }

    // 1-0:1.7.0(000560.157*kWh)
    // 1-0:1.7.0 = Actual electricity power delivered (+P) in 1 Watt resolution
    if (telegram.startsWith("1-0:1.7.0")) {
      p1_data.actual_consumption = 1000.0 * getValue(telegram, '(', '*');
    }

    // 1-0:2.7.0(000560.157*kWh)
    // 1-0:2.7.0 = Actual electricity power delivered (+P) in 1 Watt resolution
    if (telegram.startsWith("1-0:2.7.0")) {
      p1_data.actual_delivery = 1000.0 * getValue(telegram, '(', '*');
    }

    // 1-0:31.7.0(00.378*kW)
    // 1-0:31.7.0 = Instantaneous current L1 in A resolution.
    if (telegram.startsWith("1-0:31.7.0")) {
      p1_data.l1_instant_current = getValue(telegram, '(', '*');
    }

    // 1-0:21.7.0(00.378*kW)
    // 1-0:21.7.0 = Instantaneous active power L1 (+P) in W resolution
    if (telegram.startsWith("1-0:21.7.0")) {
      p1_data.l1_instant_power_consumption =
          1000 * getValue(telegram, '(', '*');
    }

    // 1-0:22.7.0(00.378*kW)
    // 1-0:22.7.0 = Instantaneous active power L1 (-P) in W resolution
    if (telegram.startsWith("1-0:22.7.0")) {
      p1_data.l1_instant_power_delivery = 1000.0 * getValue(telegram, '(', '*');
    }

    // 0-1:24.2.1(220821190000S)(08385.402*m3)
    // 0-1:24.2.1 = Last hourly value (temperature converted), gas delivered to
    // client in m3, including decimal values and capture time
    if (telegram.startsWith("0-1:24.2.1")) {
      p1_data.gas_local_timestamp =
          getText(telegram.substring(0, 25), '(', ')');
      p1_data.gas_consumption = getValue(telegram.substring(25), '(', '*');
    }

    return validCRCFound;
  }

  void print_data() {
    log_printf("Timestamp: %s\n",
               dateTime(getDatetime(p1_data.local_timestamp)).c_str());

    log_printf("Consumption Tariff 1: %.3f kWh\n",
               p1_data.consumption_1 / 1000.0);
    log_printf("Consumption Tariff 2: %.3f kWh\n",
               p1_data.consumption_2 / 1000.0);
    log_printf("Delivery Tariff 1: %.3f kWh\n", p1_data.delivery_1 / 1000.0);
    log_printf("Delivery Tariff 2: %.3f kWh\n", p1_data.delivery_2 / 1000.0);

    log_printf("Actual Tariff: %d\n", p1_data.actual_tariff);

    log_printf("Actual Consumption: %.3f kWh\n",
               p1_data.actual_consumption / 1000.0);
    log_printf("Actual Delivery: %.3f kWh\n", p1_data.actual_delivery / 1000.0);

    log_printf("Actual L1 Current: %d A\n", p1_data.l1_instant_current);
    log_printf("Actual L1 Power Consumption: %.3f kWh\n",
               p1_data.l1_instant_power_consumption / 1000.0);
    log_printf("Actual L1 Power Delivery: %.3f kWh\n",
               p1_data.l1_instant_power_delivery / 1000.0);

    log_printf("Last gas timestamp: %s\n",
               dateTime(getDatetime(p1_data.gas_local_timestamp)).c_str());
    log_printf("Last hourly gas consumption: %.3f m3\n",
               p1_data.gas_consumption);
  }

  void queue_data() {
    int conversion_ret_val;
    time_t timestamp = defaultTZ->tzTime(getDatetime(p1_data.local_timestamp));

    SensorData consumption_1_data = {timestamp, id, power_consumption_1_id};
    conversion_ret_val =
        snprintf(consumption_1_data.value, sizeof(consumption_1_data.value),
                 "%.3f", p1_data.consumption_1 / 1000.0);
    if (conversion_ret_val > 0) {
      sensor_buffer.push(consumption_1_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    }
    SensorData consumption_2_data = {timestamp, id, power_consumption_2_id};
    conversion_ret_val =
        snprintf(consumption_2_data.value, sizeof(consumption_2_data.value),
                 "%.3f", p1_data.consumption_2 / 1000.0);
    if (conversion_ret_val > 0) {
      sensor_buffer.push(consumption_2_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    }

    SensorData delivery_1_data = {timestamp, id, power_delivery_1_id};
    conversion_ret_val =
        snprintf(delivery_1_data.value, sizeof(delivery_1_data.value), "%.3f",
                 p1_data.delivery_1 / 1000.0);
    if (conversion_ret_val > 0) {
      sensor_buffer.push(delivery_1_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    }
    SensorData delivery_2_data = {timestamp, id, power_delivery_2_id};
    conversion_ret_val =
        snprintf(delivery_2_data.value, sizeof(delivery_2_data.value), "%.3f",
                 p1_data.delivery_2 / 1000.0);
    if (conversion_ret_val > 0) {
      sensor_buffer.push(delivery_2_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    }

    time_t gas_timestamp =
        defaultTZ->tzTime(getDatetime(p1_data.gas_local_timestamp));
    SensorData gas_data = {gas_timestamp, id, gas_consumption_id};
    conversion_ret_val = snprintf(gas_data.value, sizeof(gas_data.value),
                                  "%.3f", p1_data.gas_consumption);
    if (conversion_ret_val > 0) {
      sensor_buffer.push(gas_data);
      if (num_measurement_errors > 0) {
        num_measurement_errors--;
      }
    }
  }
};

P1Sensor p1_sensor("P1", 0.2,
                   JSON_ARRAY_SIZE(5) + JSON_OBJECT_SIZE(2) +
                       5 * JSON_OBJECT_SIZE(3),
                   JSON_ARRAY_SIZE(5) + JSON_OBJECT_SIZE(3) +
                       5 * JSON_OBJECT_SIZE(4));
Ticker p1_measurement_timer([]() { return p1_sensor.measure(); },
                            p1_sensor.period_s * 1e3, 0, MILLIS);
