
#include "ESPAsyncTCP.h"
#include "ESPAsyncWebServer.h"
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>

#include "Hash.h"
#include <ArduinoJson.h>
#include <CircularBuffer.h>
#include <Ticker.h>
#include <Wire.h> // I2C library
#include <ezTime.h>

#include "config.h"
#include "logging.h"

#ifdef HAS_AM2320
#include <AM232X.h>
#endif

#ifdef HAS_CCS811
#include "ccs811.h" // CCS811 library
#endif

#ifdef HAS_HDC1080
#include "ClosedCube_HDC1080.h" // HDC1080 library
#endif

//// WiFi
const char *ssid = STASSID;
const char *password = STAPSK;

//// Web Server
AsyncWebServer web_server(80);
String web_debug_info;
const char web_server_html_header[] PROGMEM = R"=====(
<!DOCTYPE HTML>
<html>
	<head>
			<title>ESP8266 Home Sensor Client</title>
	</head>
<body>
)=====";
const char web_server_html_footer[] PROGMEM = R"=====(
</body>
</html>
)=====";

//// Station
String mac_sha;
const char *location = LOCATION;

//// rest server
const char *server = SERVER_HOSTNAME;
const char *stations_endpoint = "/api/stations";
String station_endpoint, sensors_endpoint;
uint8_t station_id;
const uint8_t NUM_SENSORS = 3;
const uint8_t port = 80;
uint8 num_sending_measurement_errors = 0;

//// Time
Timezone Amsterdam;

///// Common sensor
typedef struct {
  time_t epoch;
  uint8_t sensor_id;
  uint8_t magnitude_id;
  char value[50];
} SensorData;
SensorData sensor_data;
CircularBuffer<SensorData, 255> sensor_buffer; // Keep some raw data
uint8 num_measurement_errors = 0;

#ifdef HAS_AM2320
// AM2320 Sensor
uint8_t am2320_sensor_id, am2320_temp_id, am2320_hum_id;
const char *sensor_am2320_name = "AM2320";
AM232X am2320;
const uint32_t am2320_period_s = 10;
const size_t capacity_am2320 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 2 * JSON_OBJECT_SIZE(3);
const size_t response_capacity_am2320 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 2 * JSON_OBJECT_SIZE(4);

void setup_am2320_sensor_json(JsonObject &sensor_json) {
  sensor_json["name"] = sensor_am2320_name;
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

bool parse_am2320_sensor_json(JsonObject &sensor_json_response) {
  am2320_sensor_id = sensor_json_response["id"];
  JsonArray magnitudes_json =
      sensor_json_response["magnitudes"].as<JsonArray>();
  for (JsonObject mag_json : magnitudes_json) {
    const char *name = mag_json["name"];
    if (strcmp(name, "temperature") == 0) {
      am2320_temp_id = mag_json["id"];
    } else if (strcmp(name, "humidity") == 0) {
      am2320_hum_id = mag_json["id"];
    }
  }
  log_printf("  am2320_sensor_id: %d, am2320_temp_id: %d, am2320_hum_id: %d.\n",
             am2320_sensor_id, am2320_temp_id, am2320_hum_id);
  log_header_printf(

      "AM2320 sensor_id: %d, temperature_id: %d, humidity_id: %d.",
      am2320_sensor_id, am2320_temp_id, am2320_hum_id);

  return true;
}

bool setup_am2320_sensor() {
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

void measure_am2320_sensor() {
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

  SensorData humidity_data = {now, am2320_sensor_id, am2320_hum_id};
  conversion_ret_val = snprintf(humidity_data.value,
                                sizeof(humidity_data.value), "%.3f", humidity);
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

  SensorData temperature_data = {now, am2320_sensor_id, am2320_temp_id};
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

Ticker am2320_measurement_timer(measure_am2320_sensor, am2320_period_s * 1e3, 0,
                                MILLIS);
#endif

#ifdef HAS_CCS811
// CCS811 Sensor
uint8_t ccs811_sensor_id, ccs811_eco2_id, ccs811_etvoc_id;
const char *sensor_ccs811_name = "CCS811";
// Wiring for ESP8266 NodeMCU boards: VDD to 3V3, GND to GND, SDA to D2, SCL to
// D1, nWAKE GND
CCS811 ccs811;
const uint32_t ccs811_period_s = 10;
const size_t capacity_ccs811 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 2 * JSON_OBJECT_SIZE(3);
const size_t response_capacity_ccs811 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 2 * JSON_OBJECT_SIZE(4);

void setup_ccs811_sensor_json(JsonObject &sensor_json) {
  sensor_json["name"] = sensor_ccs811_name;
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

bool parse_ccs811_sensor_json(JsonObject &sensor_json_response) {
  ccs811_sensor_id = sensor_json_response["id"];
  JsonArray magnitudes_json =
      sensor_json_response["magnitudes"].as<JsonArray>();
  for (JsonObject mag_json : magnitudes_json) {
    const char *name = mag_json["name"];
    if (strcmp(name, "eco2") == 0) {
      ccs811_eco2_id = mag_json["id"];
    } else if (strcmp(name, "etvoc") == 0) {
      ccs811_etvoc_id = mag_json["id"];
    }
  }
  log_printf(
      "  ccs811_sensor_id: %d, ccs811_eco2_id: %d, ccs811_etvoc_id: %d.\n",
      ccs811_sensor_id, ccs811_eco2_id, ccs811_etvoc_id);
  log_header_printf("CCS811 sensor_id: %d, eCO2_id: %d, eTVOC_id: %d.",
                    ccs811_sensor_id, ccs811_eco2_id, ccs811_etvoc_id);

  return true;
}

bool setup_ccs811_sensor() {
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
                    ccs811.bootloader_version(), ccs811.application_version());
  return true;
}

void measure_ccs811_sensor() {
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

  SensorData eco2_data = {now, ccs811_sensor_id, ccs811_eco2_id};
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

  SensorData etvoc_data = {now, ccs811_sensor_id, ccs811_etvoc_id};
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

Ticker ccs811_measurement_timer(measure_ccs811_sensor, ccs811_period_s * 1e3, 0,
                                MILLIS);
#endif

#ifdef HAS_HDC1080
// HAS_HDC1080 Sensor
uint8_t hdc1080_sensor_id, hdc1080_temp_id, hdc1080_hum_id;
const char *sensor_hdc1080_name = "HDC080";
ClosedCube_HDC1080 hdc1080;
const uint32_t hdc1080_period_s = 10;
const size_t capacity_hdc1080 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 2 * JSON_OBJECT_SIZE(3);
const size_t response_capacity_hdc1080 =
    JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 2 * JSON_OBJECT_SIZE(4);

void setup_hdc1080_sensor_json(JsonObject &sensor_json) {
  sensor_json["name"] = sensor_hdc1080_name;
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

bool parse_hdc1080_sensor_json(JsonObject &sensor_json_response) {
  hdc1080_sensor_id = sensor_json_response["id"];
  JsonArray magnitudes_json =
      sensor_json_response["magnitudes"].as<JsonArray>();
  for (JsonObject mag_json : magnitudes_json) {
    const char *name = mag_json["name"];
    if (strcmp(name, "temperature") == 0) {
      hdc1080_temp_id = mag_json["id"];
    } else if (strcmp(name, "humidity") == 0) {
      hdc1080_hum_id = mag_json["id"];
    }
  }
  log_printf(
      "  hdc1080_sensor_id: %d, hdc1080_temp_id: %d, hdc1080_hum_id: %d.\n",
      hdc1080_sensor_id, hdc1080_temp_id, hdc1080_hum_id);
  log_header_printf(

      "HDC1080 sensor_id: %d, temperature_id: %d, humidity_id: %d.",
      hdc1080_sensor_id, hdc1080_temp_id, hdc1080_hum_id);

  return true;
}

bool setup_hdc1080_sensor() {
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

void measure_hdc1080_sensor() {
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
  } else if ((temperature > 120) || (humidity > 99.99)) {
    log_printf("  Error reading values (%.2f, %.2f).\n", humidity, temperature);
    num_measurement_errors++;
    return;
  } else {
    SensorData humidity_data = {now, hdc1080_sensor_id, hdc1080_hum_id};
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
  }

  if (isnan(temperature)) {
    log_println("  Error reading temperature.");
    num_measurement_errors++;
  } else {
    SensorData temperature_data = {now, hdc1080_sensor_id, hdc1080_temp_id};
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
}

Ticker hdc1080_measurement_timer(measure_hdc1080_sensor, hdc1080_period_s * 1e3,
                                 0, MILLIS);
#endif

//// Post request
WiFiClient client;
HTTPClient http;
String response;
const uint32_t send_data_period_s = 5;
void send_data();
Ticker send_timer(send_data, int(send_data_period_s) * 1e3, 0, MILLIS);

////// Setup functions

void connect_to_wifi() {
  // Connect to Wi-Fi
  log_println("Connecting to WiFi");
  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA); // WiFi mode station (connect to wifi router only
  while (!WiFi.isConnected()) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();

  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    log_println("  Fail connecting");
    delay(5000);
    ESP.restart();
  }

  mac_sha = sha1(WiFi.macAddress());
  String hostname = WiFi.hostname();
  hostname.toLowerCase();
  web_debug_info_header =
      String("<h2>ESP8266 <a href='http://" + hostname + "'>" + hostname +
             "</a> home-sensor " + mac_sha + "</h2>\n<h3>Located in the " +
             location + ".</h3>\n");

  // Print ESP8266 Local IP Address
  log_printf("  Connected! IP: %s, MAC sha1: %s.",
             WiFi.localIP().toString().c_str(), mac_sha.c_str());
  log_header_printf("Connected! IP: %s, hostname: %s.",
                    WiFi.localIP().toString().c_str(), WiFi.hostname().c_str());
  log_header_printf("  MAC sha1: %s.", mac_sha.c_str());
  WiFi.setAutoReconnect(true);
}

void connect_to_time() {
  log_println("Connecting to time server");
  setDebug(ezDebugLevel_t::INFO);
  if (!waitForSync(60)) {
    Serial.println("  It took too long to update the time, restarting.");
    ESP.restart();
  }
  setInterval(60 * 60); // 1h in seconds

  log_println("  UTC: " + UTC.dateTime());

  Amsterdam.setLocation("Europe/Amsterdam");
  log_println("  Amsterdam time: " + Amsterdam.dateTime());
  log_header_printf("Connection stablished with the time server.");
  log_header_printf("  Amsterdam time: %s.", Amsterdam.dateTime().c_str());
}

bool setup_station() {
  // Post Data
  if (WiFi.status() != WL_CONNECTED) {
    connect_to_wifi();
    return false;
  }

  log_println("setup_station");

  // Prepare JSON document
  const size_t capacity = JSON_OBJECT_SIZE(2);
  DynamicJsonDocument station_json(capacity + 50);

  station_json["token"] = mac_sha;
  station_json["location"] = location;

  // Serialize JSON document
  String station_data;
  serializeJson(station_json, station_data);

  // post data, if the response is 201 then it was created
  // If it was 200 then it was already there.
  int post_httpCode;

  http.begin(client, server, port, stations_endpoint);
  http.addHeader("Content-Type", "application/json");
  const char *headerNames[] = {"Location"};
  http.collectHeaders(headerNames,
                      sizeof(headerNames) / sizeof(headerNames[0]));

  post_httpCode = http.POST(station_data); // Send the request
  log_printf("  POST HTTP code: %d.\n", post_httpCode);
  switch (post_httpCode) {
  case HTTP_CODE_OK: // Station already existed
    break;
  case HTTP_CODE_CREATED: // Station created
    break;
  default:
    http.end();
    return false;
  }

  station_id = http.header("Location").toInt();
  station_endpoint = String(stations_endpoint) + "/" + station_id;
  sensors_endpoint = String(stations_endpoint) + "/" + station_id + "/sensors";

  log_printf("  station_id: %d.\n", station_id);
  log_header_printf("station_id: %d, POST code: %d.", station_id,
                    post_httpCode);

  http.end();
  return true;
}

bool setup_sensors() {
  if (WiFi.status() != WL_CONNECTED) {
    connect_to_wifi();
    return false;
  }

  log_println("setup_sensors");

  // Prepare JSON document
  size_t capacity = JSON_ARRAY_SIZE(NUM_SENSORS);
#ifdef HAS_AM2320
  capacity += capacity_am2320;
#endif
#ifdef HAS_CCS811
  capacity += capacity_ccs811;
#endif
#ifdef HAS_HDC1080
  capacity += capacity_hdc1080;
#endif
  DynamicJsonDocument sensors_json(capacity + 200);

  size_t response_capacity = JSON_ARRAY_SIZE(NUM_SENSORS);
#ifdef HAS_AM2320
  response_capacity += response_capacity_am2320;
#endif
#ifdef HAS_CCS811
  response_capacity += response_capacity_ccs811;
#endif
#ifdef HAS_HDC1080
  response_capacity += response_capacity_hdc1080;
#endif
  DynamicJsonDocument sensors_json_response(response_capacity + 200);

#ifdef HAS_AM2320
  JsonObject am2320_json = sensors_json.createNestedObject();
  setup_am2320_sensor_json(am2320_json);
#endif
#ifdef HAS_CCS811
  JsonObject ccs811_json = sensors_json.createNestedObject();
  setup_ccs811_sensor_json(ccs811_json);
#endif
#ifdef HAS_HDC1080
  JsonObject hdc1080_json = sensors_json.createNestedObject();
  setup_hdc1080_sensor_json(hdc1080_json);
#endif

  // Serialize JSON document
  String sensors_data;
  serializeJson(sensors_json, sensors_data);

  // put data, if the response is 204 then it all went well
  int get_httpCode, put_httpCode;
  http.begin(client, server, port, sensors_endpoint);
  put_httpCode = http.PUT(sensors_data);
  log_printf("  PUT HTTP code: %d.\n", put_httpCode);
  log_header_printf("setup sensors PUT HTTP code: %d", put_httpCode);
  switch (put_httpCode) {
  case HTTP_CODE_NO_CONTENT: // OK, GET sensors
    http.end();
    http.begin(client, server, port, sensors_endpoint);
    get_httpCode = http.GET();
    log_printf("  GET HTTP code: %d.\n", get_httpCode);
    log_header_printf("setup sensors GET HTTP code: %d", get_httpCode);
    break;
  default:
    http.end();
    return false;
  }

  response = http.getString(); // Get the response payload
  http.end();
  // log_printf("  rest_server response: %s.\n", response.c_str());

  deserializeJson(sensors_json_response, response);
  JsonArray sensors_json_out = sensors_json_response.as<JsonArray>();

  for (JsonObject sensor_json : sensors_json_out) {
    const char *name = sensor_json["name"];
#ifdef HAS_AM2320
    if (strcmp(name, sensor_am2320_name) == 0) {
      parse_am2320_sensor_json(sensor_json);
    }
#endif
#ifdef HAS_CCS811
    if (strcmp(name, sensor_ccs811_name) == 0) {
      parse_ccs811_sensor_json(sensor_json);
    }
#endif
#ifdef HAS_HDC1080
    if (strcmp(name, sensor_hdc1080_name) == 0) {
      parse_hdc1080_sensor_json(sensor_json);
    }
#endif
  }

  return true;
}

bool setup_internal_sensors() {
  bool res = true;
#ifdef HAS_AM2320
  res = res && setup_am2320_sensor();
#endif

#ifdef HAS_HDC1080
  res = res && setup_hdc1080_sensor();
#endif

#ifdef HAS_CCS811
  res = res && setup_ccs811_sensor();
#endif

  return res;
}

void setup_web_server() {
  log_println("setup_server");

  // Web server
  web_server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    if (!log_buffer.isEmpty()) {
      web_debug_info = "";
      using index_t = decltype(log_buffer)::index_t;
      for (index_t i = 0; i < log_buffer.size(); i++) {
        LogData log_record = log_buffer[i];
        String message = String(log_record.message);
        message.replace("\n", "");
        message.replace(" ", "&nbsp;");

        web_debug_info +=
            UTC.dateTime(log_record.epoch) + " - " + message + "<br>\n";
      }
    }
    request->send(200, "text/html",
                  String(web_server_html_header) + web_debug_info_header +
                      "<hr>" + web_debug_info + web_server_html_footer);
  });

  web_server.onNotFound([](AsyncWebServerRequest *request) {
    Serial.println("404.");
    request->send(404, "text/plain", "Not found");
  });

  // Start server
  web_server.begin();
  log_println("  done.");
}

////// Send data functions
bool post_measurement(String &data, String endpoint) {
  // Post Data
  if (WiFi.status() != WL_CONNECTED) {
    connect_to_wifi();
    return false;
  }

  http.begin(client, server, port, endpoint);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(data); // Send the request
  http.end();
  switch (httpCode) {
  case HTTP_CODE_CREATED:
    if (num_sending_measurement_errors > 0) {
      num_sending_measurement_errors--;
    }
    return true;
  default:
    log_printf(("  post_measurement HTTP Error code (%d): " +
                http.errorToString(httpCode))
                   .c_str(),
               httpCode);
    num_sending_measurement_errors++;
    return false;
  }
}

#ifdef DONT_SEND_DATA
void send_data() {}
#else
void send_data() {
  if (sensor_buffer.isEmpty()) {
    return;
  }
  using index_t = decltype(sensor_buffer)::index_t;

  const index_t num_measurements = sensor_buffer.size();
  log_printf("Sending %d measurements...\n", num_measurements);

  // Prepare JSON document
  const size_t capacity = JSON_ARRAY_SIZE(num_measurements) +
                          num_measurements * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument list_measurement(capacity + 200 * num_measurements);

  for (index_t i = 0; i < num_measurements; i++) {
    sensor_data = sensor_buffer[i];
    JsonObject data_0 = list_measurement.createNestedObject();
    data_0["sensor_id"] = sensor_data.sensor_id;
    data_0["magnitude_id"] = sensor_data.magnitude_id;
    data_0["timestamp"] = sensor_data.epoch;
    data_0["value"] = sensor_data.value;
  }

  // Serialize JSON document
  String post_data;
  serializeJson(list_measurement, post_data);

  const bool success =
      post_measurement(post_data, station_endpoint + "/measurements");

  if (success) {
    log_println("  Data sent successfully.");
    sensor_buffer.clear();
  } else {
    log_println("  Data was not sent.");
  }
}
#endif

void setup() {
  Serial.begin(115200);

  Wire.begin();

  connect_to_wifi();

  connect_to_time();

  setup_web_server();

  uint8_t num_tries = 0;

#ifndef DONT_SEND_DATA
  while (!setup_station()) {
    if (num_tries < 100) {
      log_println("Retrying to setup the station.");
      delay(1000);
      num_tries++;
    } else {
      Serial.println("Too many retries to setup_station: restarting.");
      ESP.restart();
    }
  }

  num_tries = 0;
  while (!setup_sensors()) {
    if (num_tries < 100) {
      log_println("Retrying to setup the sensors.");
      delay(1000);
      num_tries++;
    } else {
      Serial.println("Too many retries to setup_sensors: restarting.");
      ESP.restart();
    }
  }
#endif

  num_tries = 0;
  while (!setup_internal_sensors()) {
    if (num_tries < 100) {
      log_println("Retrying to setup the internal sensors.");
      delay(1000);
      num_tries++;
    } else {
      Serial.println("Too many retries to setup_internal_sensors: restarting.");
      ESP.restart();
    }
  }

  // Timer
#ifdef HAS_AM2320
  am2320_measurement_timer.start();
#endif
#ifdef HAS_CCS811
  ccs811_measurement_timer.start();
#endif
#ifdef HAS_HDC1080
  hdc1080_measurement_timer.start();
#endif
  send_timer.start();
}

void loop() {
  // Update time if needed
  events();

  if (num_measurement_errors > 100) {
    Serial.println("Too many measurement errors: restarting.");
    ESP.restart();
  }
  if (num_sending_measurement_errors > 100) {
    Serial.println("Too many errors sending measurements: restarting.");
    ESP.restart();
  }

  // Update timer
#ifdef HAS_AM2320
  am2320_measurement_timer.update();
#endif
#ifdef HAS_CCS811
  ccs811_measurement_timer.update();
#endif
#ifdef HAS_HDC1080
  hdc1080_measurement_timer.update();
#endif
  send_timer.update();
}
