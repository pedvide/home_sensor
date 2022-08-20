
#include "ESPAsyncTCP.h"
#include "ESPAsyncWebServer.h"
#include "LittleFS.h"
#include <ArduinoOTA.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <functional>

#include "Hash.h"
#include <ArduinoJson.h>
#include <CircularBuffer.h>
#include <Ticker.h>
#include <Wire.h> // I2C library
#include <ezTime.h>

#include "common_sensor.h"
#include "config.h"
#include "logging.h"

#ifdef HAS_AM2320
#include <AM2320Sensor.h>
#endif

#ifdef HAS_CCS811
#include "CCS811Sensor.h"
#endif

#ifdef HAS_HDC1080
#include "HDC1080Sensor.h"
#endif

#ifdef HAS_HP303B
#include <HP303BSensor.h>
#endif

//// WiFi
const char *ssid PROGMEM = STASSID;
const char *password PROGMEM = STAPSK;

//// Web Server
AsyncWebServer web_server(80);
bool requested_restart = false;
const char web_server_html_header[] PROGMEM = R"=====(
<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="style.css">
<title>ESP8266 Home Sensor Station %s</title>
</head>
<body>
<header>
<h1>ESP8266 home-sensor station <a href='http://%s'>%s</a></h1>
<h3>Located in the %s.</h3>
<div class="button-bar">
  <div class="button-holder">
    <a class='button' id='btn-restart' href='http://%s/restart'>Restart</a>
  </div>
  <div class="button-holder">
    <a class='button' id='btn-blink' href='http://%s/blink'>Blink</a>
  </div>
  <div class="button-holder">
    <a class='button' id='btn-dashboard' href='http://home-sensor.home/grafana/d/h45MReWRk/home-sensor?orgId=1&refresh=5m' target="_blank">Dashboard</a>
  </div>
  <div class="button-holder">
    <a class='button' id='btn-homesensor' href='http://home-sensor.home' target="_blank">All Stations</a>
  </div>
</div>
</header>
)=====";

const char web_server_html_footer[] PROGMEM = R"=====(
<footer>
Home Sensor Project
</footer>
</body>
</html>
)=====";

//// Station
String mac_sha, hostname;
#ifdef LOCATION
const char *location PROGMEM = LOCATION;
#else
const char *location PROGMEM = "test";
#endif

//// rest server
const char *server PROGMEM = SERVER_HOSTNAME;
const char *stations_endpoint PROGMEM = "/api/stations";
String station_endpoint, sensors_endpoint;
uint8_t station_id;
const uint8_t port = 80;
uint8 num_sending_measurement_errors = 0;

//// Time
Timezone Amsterdam;

//// Sensors
Sensor *sensors[NUM_SENSORS] = {
#ifdef HAS_AM2320
    &am2320_sensor,
#endif
#ifdef HAS_CCS811
    &ccs811_sensor,
#endif
#ifdef HAS_HDC1080
    &hdc1080_sensor,
#endif
#ifdef HAS_HP303B
    &hp303b_sensor,
#endif
};

// Sensor timers
Ticker *sensor_timers[NUM_SENSORS] = {
#ifdef HAS_AM2320
    &am2320_measurement_timer,
#endif
#ifdef HAS_CCS811
    &ccs811_measurement_timer,
#endif
#ifdef HAS_HDC1080
    &hdc1080_measurement_timer,
#endif
#ifdef HAS_HP303B
    &hp303b_measurement_timer,
#endif
};

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
  log_println(F("Connecting to WiFi"));
  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA); // WiFi mode station (connect to wifi router only
  while (!WiFi.isConnected()) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();

  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    log_println(F("  Fail connecting"));
    delay(5000);
    ESP.restart();
  }

  mac_sha = sha1(WiFi.macAddress());
  hostname = WiFi.hostname();
  hostname.toLowerCase();

  // Print ESP8266 Local IP Address
  log_printf("  Connected! IP: %s, MAC sha1: %s.\n",
             WiFi.localIP().toString().c_str(), mac_sha.c_str());
  log_header_printf("IP: %s, hostname: %s, chip ID: %x.",
                    WiFi.localIP().toString().c_str(), hostname.c_str(),
                    ESP.getChipId());
  log_header_printf("  MAC sha1: %s.", mac_sha.c_str());
  WiFi.setAutoReconnect(true);
}

void setup_OTA() {
  ArduinoOTA.onStart([]() {
    LittleFS.end();
    log_println(F("Starting the OTA update."));
  });

  ArduinoOTA.onEnd([]() { log_println(F("Finished the OTA update.")); });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    static uint8_t last_perc_progress = 0;
    uint8_t perc_progress = (progress / (total / 100));
    if (((perc_progress % 20) == 0) && (perc_progress > last_perc_progress)) {
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      log_printf("OTA progress: %u%%.\n", perc_progress);
      last_perc_progress = perc_progress;
    }
  });

  ArduinoOTA.onError([](ota_error_t error) {
    log_printf("OTA Error (%u): ", error);
    if (error == OTA_AUTH_ERROR)
      log_println(F("Auth Failed"));
    else if (error == OTA_BEGIN_ERROR)
      log_println(F("Begin Failed"));
    else if (error == OTA_CONNECT_ERROR)
      log_println(F("Connect Failed"));
    else if (error == OTA_RECEIVE_ERROR)
      log_println(F("Receive Failed"));
    else if (error == OTA_END_ERROR)
      log_println(F("End Failed"));
  });

  ArduinoOTA.begin();
  log_header_printf("OTA enabled.");
}

bool connect_to_time() {
  log_println(F("Connecting to time server"));
  setDebug(ezDebugLevel_t::INFO);
  setServer(NTP_SERVER_HOSTNAME);

  if (!Amsterdam.setCache(0)) {
    Amsterdam.setLocation("Europe/Berlin");
  }
  Amsterdam.setDefault();

  if (!waitForSync(10)) {
    return false;
  }
  setInterval(60 * 60); // 1h in seconds

  log_println("  UTC: " + UTC.dateTime());
  log_println("  Amsterdam time: " + Amsterdam.dateTime());
  log_header_printf("Connection stablished with the time server (%s). Using "
                    "Amsterdam time.\n",
                    UTC.dateTime().c_str());

  return true;
}

bool setup_station() {
  // Post Data
  if (WiFi.status() != WL_CONNECTED) {
    connect_to_wifi();
    return false;
  }

  log_println("setup_station");

  // Prepare JSON document
  const size_t capacity = JSON_OBJECT_SIZE(3);
  DynamicJsonDocument station_json(capacity + 50);

  station_json["token"] = mac_sha;
  station_json["location"] = location;
  station_json["hostname"] = hostname;

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
  log_header_printf(
      "Connected to server at %s%s, station_id: %d (POST code: %d).", server,
      stations_endpoint, station_id, post_httpCode);

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
  for (auto sensor : sensors) {
    capacity += sensor->capacity;
  }
  // #ifdef HAS_AM2320
  //   capacity += am2320_sensor.capacity;
  // #endif
  // #ifdef HAS_CCS811
  //   capacity += ccs811_sensor.capacity;
  // #endif
  // #ifdef HAS_HDC1080
  //   capacity += capacity_hdc1080;
  // #endif
  // #ifdef HAS_HP303B
  //   capacity += capacity_hp303b;
  // #endif
  DynamicJsonDocument sensors_json(capacity + 200);

  size_t response_capacity = JSON_ARRAY_SIZE(NUM_SENSORS);
  for (auto sensor : sensors) {
    response_capacity += sensor->response_capacity;
  }
  // #ifdef HAS_AM2320
  //   response_capacity += am2320_sensor.response_capacity;
  // #endif
  // #ifdef HAS_CCS811
  //   response_capacity += response_capacity_ccs811;
  // #endif
  // #ifdef HAS_HDC1080
  //   response_capacity += response_capacity_hdc1080;
  // #endif
  // #ifdef HAS_HP303B
  //   response_capacity += response_capacity_hp303b;
  // #endif
  DynamicJsonDocument sensors_json_response(response_capacity + 200);
  for (auto sensor : sensors) {
    JsonObject sensor_json = sensors_json.createNestedObject();
    sensor->setup_json(sensor_json);
  }

  // Serialize JSON document
  String sensors_data;
  serializeJson(sensors_json, sensors_data);

  // put data, if the response is 204 then it all went well
  int get_httpCode, put_httpCode;
  http.begin(client, server, port, sensors_endpoint);
  put_httpCode = http.PUT(sensors_data);
  log_printf("  PUT HTTP code: %d.\n", put_httpCode);
  log_header_printf("Connected to server at %s%s, setup sensors: PUT code: %d.",
                    server, sensors_endpoint.c_str(), put_httpCode);
  switch (put_httpCode) {
  case HTTP_CODE_NO_CONTENT: // OK, GET sensors
    http.end();
    http.begin(client, server, port, sensors_endpoint);
    get_httpCode = http.GET();
    log_printf("  GET HTTP code: %d.\n", get_httpCode);
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
    for (auto sensor : sensors) {
      if (strcmp(name, sensor->name) == 0) {
        sensor->parse_json(sensor_json);
        break;
      }
    }
  }

  return true;
}

bool setup_internal_sensors() {
  bool res = true;
  for (auto sensor : sensors) {
    res = res && sensor->setup();
  }
  return res;
}

void setup_web_server() {
  log_println(F("setup_server"));

  // Web server
  web_server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    AsyncResponseStream *response = request->beginResponseStream("text/html");
    response->printf_P(web_server_html_header, hostname.c_str(),
                       hostname.c_str(), hostname.c_str(), location,
                       hostname.c_str(), hostname.c_str());

    response->println(
        F("<main><h2>Logs</h2>\n<h3>Setup</h3>\n<ol class='header-log'>"));

    if (!log_header_buffer.isEmpty()) {
      using index_t = decltype(log_header_buffer)::index_t;
      for (index_t i = 0; i < log_header_buffer.size(); i++) {
        String msg = String(log_header_buffer[i].message);
        msg.replace("  ", "&nbsp;&nbsp;");
        msg.replace("\n", "");
        response->printf("<li class='log-msg'><time class='log-dt'>%s</time> "
                         "<span class='log-text'>%s</span></li>\n",
                         Amsterdam.dateTime(log_header_buffer[i].epoch).c_str(),
                         msg.c_str());
      }
    }

    response->println(F("</ol>\n<h3>Live</h3>\n<ol class='main-log'>"));

    if (!log_buffer.isEmpty()) {
      using index_t = decltype(log_buffer)::index_t;
      for (index_t i = 0; i < log_buffer.size(); i++) {
        String msg = String(log_buffer[i].message);
        msg.replace("  ", "&nbsp;&nbsp;");
        msg.replace("\n", "");
        response->printf("<li class='log-msg'><time class='log-dt'>%s</time> "
                         "<span class='log-text'>%s</span></li>\n",
                         Amsterdam.dateTime(log_buffer[i].epoch).c_str(),
                         msg.c_str());
      }
    }

    response->println(F("</ol>\n</main>"));
    response->printf_P(web_server_html_footer);
    request->send(response);
  });

  web_server.on("/style.css", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/style.css", "text/css");
  });

  web_server.on("/restart", HTTP_GET, [](AsyncWebServerRequest *request) {
    requested_restart = true;
    request->redirect("/");
  });

  web_server.on("/blink", HTTP_GET, [](AsyncWebServerRequest *request) {
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    request->redirect("/");
  });

  web_server.on("/health", HTTP_GET, [](AsyncWebServerRequest *request) {
    AsyncWebServerResponse *response =
        request->beginResponse(200, F("text/plain"), F("Ok"));
    response->addHeader("Access-Control-Allow-Origin", "*");
    request->send(response);
  });

  web_server.onNotFound([](AsyncWebServerRequest *request) {
    Serial.println(F("404."));
    request->send(404, F("text/plain"), F("Not found"));
  });

  // Start server
  web_server.begin();
  log_println("  done.");
}

void log_heap_usage() {
  uint32_t hfree = 0;
  uint16_t hmax = 0;
  uint8_t hfrag = 0;
  ESP.getHeapStats(&hfree, &hmax, &hfrag);
  log_printf(
      "Free RAM: %d kB, largest contiguous: %d kB (fragmentation: %d%%).\n",
      hfree / 1024, hmax / 1024, hfrag);
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
    log_printf("  post_measurement HTTP Error code (%d): %s.", httpCode,
               http.errorToString(httpCode).c_str());
    num_sending_measurement_errors++;
    return false;
  }
}

#ifdef DONT_SEND_DATA
void send_data() {}
#else
void send_data() {

  log_heap_usage();

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
    log_println(F("  Data sent successfully."));
    sensor_buffer.clear();
  } else {
    log_println(F("  Data was not sent."));
  }
}
#endif

void retry(std::function<bool()> func, const __FlashStringHelper *info,
           uint8_t max_retries = 10) {
  uint8_t num_tries = 0;
  while (!func()) {
    if (num_tries < max_retries) {
      log_printf("Retrying '%s'.\n", info);
      if (requested_restart) {
        delay(10);
        ESP.restart();
      }
      ArduinoOTA.handle();
      delay(1000);
      num_tries++;
    } else {
#ifdef ALLOW_SENSOR_FAILURES
      log_printf("Too many retries for '%S'. Continuing.\n", info);
      return;
#else
      log_printf("Too many retries for '%S'. Restarting.\n", info);
      delay(1000);
      ESP.restart();
#endif
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); // LED pin is active low

  Serial.begin(115200);

  Wire.begin();

  LittleFS.begin();

  log_header_printf("Last restart due to %s.", ESP.getResetReason().c_str());
  log_header_printf("CPU freq: %d MHz, Flash size: %d kB, Sketch size: %d kB "
                    "(free: %d kB), Free RAM: %d kB.",
                    ESP.getCpuFreqMHz(), ESP.getFlashChipRealSize() / 1024,
                    ESP.getSketchSize() / 1024, ESP.getFreeSketchSpace() / 1024,
                    ESP.getFreeHeap() / 1024);

  connect_to_wifi();

  setup_web_server();

  setup_OTA();

  retry(&connect_to_time, F("connect to time server"));

#ifndef DONT_SEND_DATA
  retry(&setup_station, F("setup the station"));
  retry(&setup_sensors, F("setup the sensors"));
#endif

  retry(&setup_internal_sensors, F("setup the internal sensors"));

  // Timer
  for (auto sensor_timer : sensor_timers) {
    sensor_timer->start();
  }

  send_timer.start();

  digitalWrite(LED_BUILTIN, HIGH); // LED pin is active low
}

void loop() {
  // Update time if needed
  events();

  // Deal with OTA
  ArduinoOTA.handle();

  if (requested_restart) {
    delay(10);
    ESP.restart();
  }

#ifndef ALLOW_SENSOR_FAILURES
  if (num_measurement_errors > 100) {
    Serial.println(F("Too many measurement errors: restarting."));
    ESP.restart();
  }
#endif
  if (num_sending_measurement_errors > 100) {
    Serial.println(F("Too many errors sending measurements: restarting."));
    ESP.restart();
  }

  // Update timer
  for (auto sensor_timer : sensor_timers) {
    sensor_timer->update();
  }
  send_timer.update();
}
