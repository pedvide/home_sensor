
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include "ESPAsyncTCP.h"
#include "ESPAsyncWebServer.h"

#include <Adafruit_AM2320.h>
#include <ezTime.h>
#include <CircularBuffer.h>
#include "Hash.h"
#include <Ticker.h>
#include <ArduinoJson.h>

#include "config.h"
#include "logging.h"

//// WiFi
const char *ssid = STASSID;
const char *password = STAPSK;

//// Web Server
AsyncWebServer web_server(80);
String web_debug_info_header, web_debug_info;
const char web_server_html_header[] PROGMEM = R"=====(
<!DOCTYPE HTML><html>
<head>
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
const char *location = "living room";

//// rest server
const char *server = SERVER_HOSTNAME;
const char *stations_endpoint = "/api/stations";
String station_endpoint, sensors_endpoint;
uint8_t station_id;
uint8_t sensor_ids[1];
const uint8_t port = 80;

//// Time
Timezone Amsterdam;

///// Common sensor
const uint32_t sensor_period_s = 10;
void measure_sensors();
Ticker measurement_timer(measure_sensors, sensor_period_s * 1e3, 0, MILLIS);
typedef struct
{
  time_t epoch;
  uint8_t sensor_id;
  uint8_t magnitude_id;
  char value[50];
} SensorData;
SensorData sensor_data;
CircularBuffer<SensorData, 255> sensor_buffer; // Keep some raw data
uint8 num_measurement_errors = 0;

// AM2320 Sensor
uint8_t am2320_sensor_id, am2320_temp_id, am2320_hum_id;
const char *sensor_am2320_name = "AM2320";
float temperature, humidity;
Adafruit_AM2320 am2320 = Adafruit_AM2320();

//// Post request
WiFiClient client;
HTTPClient http;
String response;
// Updates readings every x/2 seconds
void send_data();
Ticker send_timer(send_data, int(sensor_period_s / 2) * 1e3, 0, MILLIS);

////// Setup functions

void connect_to_wifi()
{
  // Connect to Wi-Fi
  log_println("Connecting to WiFi");
  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA); //WiFi mode station (connect to wifi router only
  while (!WiFi.isConnected())
  {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();

  while (WiFi.waitForConnectResult() != WL_CONNECTED)
  {
    log_println("Fail connecting");
    delay(5000);
    ESP.restart();
  }

  mac_sha = sha1(WiFi.macAddress());
  web_debug_info_header = String("<h2>ESP8266 home-sensor " + mac_sha + "</h2>\n<h3>Located in the " + location + ".</h3><br>");

  // Print ESP8266 Local IP Address
  log_print("Connected!");
  log_print("IP: ");
  log_println(WiFi.localIP().toString());
  log_print("MAC sha1: ");
  log_println(mac_sha);
  WiFi.setAutoReconnect(true);
}

void connect_to_time()
{
  setDebug(ezDebugLevel_t::INFO);
  waitForSync();
  setInterval(60 * 60); // 1h in seconds

  log_println("UTC: " + UTC.dateTime());

  Amsterdam.setLocation("Europe/Amsterdam");
  log_println("Amsterdam time: " + Amsterdam.dateTime());
}

bool setup_station()
{
  // Post Data
  if (WiFi.status() != WL_CONNECTED)
  {
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
  http.collectHeaders(headerNames, sizeof(headerNames) / sizeof(headerNames[0]));

  post_httpCode = http.POST(station_data); //Send the request
  log_printf("  POST HTTP code: %d.\n", post_httpCode);
  switch (post_httpCode)
  {
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

  http.end();
  return true;
}

bool setup_am2320_sensor_json(JsonObject &am2320_json)
{
  am2320_json["name"] = sensor_am2320_name;
  JsonArray sensor_1_in_magnitudes = am2320_json.createNestedArray("magnitudes");

  JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
  mag1_in["name"] = "temperature";
  mag1_in["unit"] = "C";
  mag1_in["precision"] = 0.1;

  JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
  mag2_in["name"] = "humidity";
  mag2_in["unit"] = "%";
  mag2_in["precision"] = 0.1;

  return true;
}

bool parse_am2320_sensor_json(JsonObject &am2320_json_response)
{
  am2320_sensor_id = am2320_json_response["id"];
  JsonArray magnitudes_json = am2320_json_response["magnitudes"].as<JsonArray>();
  for (JsonObject mag_json : magnitudes_json)
  {
    const char *name = mag_json["name"];
    if (strcmp(name, "temperature") == 0)
    {
      am2320_temp_id = mag_json["id"];
    }
    else if (strcmp(name, "humidity") == 0)
    {
      am2320_hum_id = mag_json["id"];
    }
  }
  log_printf("  am2320_sensor_id: %d, am2320_temp_id: %d, am2320_hum_id: %d.\n",
             am2320_sensor_id, am2320_temp_id, am2320_hum_id);

  return true;
}

bool setup_am2320_sensor()
{
  am2320.begin();
  delay(500);

  return true;
}

bool setup_sensors()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

  log_println("setup_sensors");

  // Prepare JSON document
  const size_t capacity_am2320 = JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 2 * JSON_OBJECT_SIZE(3);
  const size_t capacity = JSON_ARRAY_SIZE(1) + capacity_am2320;
  DynamicJsonDocument sensors_json(capacity + 200);
  const size_t response_capacity_am2320 = JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 2 * JSON_OBJECT_SIZE(4);
  const size_t response_capacity = JSON_ARRAY_SIZE(1) + response_capacity_am2320;
  DynamicJsonDocument sensors_json_response(response_capacity + 200);

  JsonObject am2320_json = sensors_json.createNestedObject();
  setup_am2320_sensor_json(am2320_json);

  // Serialize JSON document
  String sensors_data;
  serializeJson(sensors_json, sensors_data);

  // put data, if the response is 204 then it all went well
  int get_httpCode, put_httpCode;
  http.begin(client, server, port, sensors_endpoint);
  put_httpCode = http.PUT(sensors_data);
  log_printf("  PUT HTTP code: %d.\n", put_httpCode);
  switch (put_httpCode)
  {
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

  response = http.getString(); //Get the response payload
  http.end();
  // log_printf("  rest_server response: %s.\n", response.c_str());

  deserializeJson(sensors_json_response, response);
  JsonArray sensors_json_out = sensors_json_response.as<JsonArray>();

  for (JsonObject sensor_json : sensors_json_out)
  {
    const char *name = sensor_json["name"];
    if (strcmp(name, sensor_am2320_name) == 0)
    {
      parse_am2320_sensor_json(sensor_json);
    }
  }

  // setup AM2320 sensor
  setup_am2320_sensor();

  // Collect all sensor_ids
  sensor_ids[0] = am2320_sensor_id;

  return true;
}

void setup_server()
{
  log_println("setup_server");

  // Web server
  web_server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    if (!log_buffer.isEmpty())
    {
      web_debug_info = "";
      using index_t = decltype(log_buffer)::index_t;
      for (index_t i = 0; i < log_buffer.size(); i++)
      {
        log_record = log_buffer[i];
        String message = String(log_record.message);
        message.replace("\n", "");
        web_debug_info += UTC.dateTime(log_record.epoch) + " - " + message + "<br>";
      }
    }
    request->send(200, "text/html",
                  String(web_server_html_header) + web_debug_info_header + web_debug_info + web_server_html_footer);
  });

  web_server.onNotFound([](AsyncWebServerRequest *request) {
    Serial.println("404.");
    request->send(404, "text/plain", "Not found");
  });

  // Start server
  web_server.begin();
  log_println("  done.");
}

////// Measurement functions
void measure_am2320_sensor()
{
  log_println("Measuring AM2320...");
  int conversion_ret_val;
  time_t now = UTC.now();
  // sensor
  humidity = am2320.readHumidity();
  temperature = am2320.readTemperature();

  if (isnan(humidity))
  {
    log_println("  Error reading humidity.");
    num_measurement_errors++;
  }
  else
  {
    SensorData humidity_data = {now, am2320_sensor_id, am2320_hum_id};
    conversion_ret_val = snprintf(humidity_data.value, sizeof(humidity_data.value), "%.3f", humidity);
    if (conversion_ret_val > 0)
    {
      log_printf("  Humidity: %.2f %%.\n", humidity);
      sensor_buffer.push(humidity_data);
      if (num_measurement_errors > 0)
      {
        num_measurement_errors--;
      }
    }
    else
    {
      log_printf("  Problem converting humidity (%.2f %%) to char[].\n", humidity);
    }
  }

  if (isnan(temperature))
  {
    log_println("  Error reading temperature.");
    num_measurement_errors++;
  }
  else
  {
    SensorData temperature_data = {now, am2320_sensor_id, am2320_temp_id};
    conversion_ret_val = snprintf(temperature_data.value, sizeof(temperature_data.value), "%.3f", temperature);
    if (conversion_ret_val > 0)
    {
      log_printf("  Temperature: %.2f C.\n", temperature);
      sensor_buffer.push(temperature_data);
      if (num_measurement_errors > 0)
      {
        num_measurement_errors--;
      }
    }
    else
    {
      log_printf("  Problem converting temperature (%.2f C) to char[].\n", temperature);
    }
  }
}

void measure_sensors()
{
  measure_am2320_sensor();
}

////// Send data functions
bool post_measurement(String &data, String endpoint)
{
  // Post Data
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

  http.begin(client, server, port, endpoint);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(data); //Send the request
  http.end();
  switch (httpCode)
  {
  case HTTP_CODE_CREATED:
    return true;
  default:
    log_println("  post_measurement HTTP Error code: " + http.errorToString(httpCode));
    return false;
  }
}

void send_data()
{
  if (sensor_buffer.isEmpty())
  {
    return;
  }
  using index_t = decltype(sensor_buffer)::index_t;

  const index_t num_measurements = sensor_buffer.size();
  log_printf("Sending %d measurements...\n", num_measurements);

  // Prepare JSON document
  const size_t capacity = JSON_ARRAY_SIZE(num_measurements) + num_measurements * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument list_measurement(capacity + 200 * num_measurements);

  for (index_t i = 0; i < num_measurements; i++)
  {
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

  const bool success = post_measurement(post_data, station_endpoint + "/measurements");

  if (success)
  {
    log_println("  Data sent successfully.");
    sensor_buffer.clear();
  }
  else
  {
    log_println("  Data was not sent.");
  }
}

void setup()
{
  Serial.begin(115200);

  connect_to_wifi();

  connect_to_time();

  setup_server();

  uint8_t num_tries = 0;
  while (!setup_station())
  {
    if (num_tries < 100)
    {
      delay(1000);
      num_tries++;
    }
    else
    {
      Serial.println("Too many retries to setup_station: restarting.");
      ESP.restart();
    }
  }

  num_tries = 0;
  while (!setup_sensors())
  {
    if (num_tries < 100)
    {
      delay(1000);
      num_tries++;
    }
    else
    {
      Serial.println("Too many retries to setup_sensors: restarting.");
      ESP.restart();
    }
  }

  // Timer
  measurement_timer.start();
  send_timer.start();
}

void loop()
{
  // Update time if needed
  events();

  if (num_measurement_errors > 100)
  {
    Serial.println("Too many measurement errors: restarting.");
    ESP.restart();
  }

  // Update timer
  measurement_timer.update();
  send_timer.update();
}
