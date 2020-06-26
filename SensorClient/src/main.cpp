
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Adafruit_AM2320.h>
#include <ezTime.h>
#include <CircularBuffer.h>
#include "Hash.h"
#include <Ticker.h>
#include <ArduinoJson.h>

#include "config.h"

String mac_sha;

//// WiFi
const char *ssid = STASSID;
const char *password = STAPSK;

const char *location = "living room";

//// Main server
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
  uint8_t magnitude_id;
  char value[50];
} SensorData;
SensorData sensor_data;
CircularBuffer<SensorData, 255> sensor_buffer; // Keep some raw data

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
  Serial.println("Connecting to WiFi");
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
    Serial.println("Fail connecting");
    delay(5000);
    ESP.restart();
  }

  mac_sha = sha1(WiFi.macAddress());

  // Print ESP8266 Local IP Address
  Serial.println("Connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("MAC sha1: ");
  Serial.println(mac_sha);
  WiFi.setAutoReconnect(true);
}

void connect_to_time()
{
  setDebug(ezDebugLevel_t::INFO);
  waitForSync();
  setInterval(60 * 60); // 1h in seconds

  Serial.println("UTC: " + UTC.dateTime());

  Amsterdam.setLocation("Europe/Amsterdam");
  Serial.println("Amsterdam time: " + Amsterdam.dateTime());
}

bool setup_station()
{
  // Post Data
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

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
  Serial.printf("POST HTTP code: %d.\n", post_httpCode);
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

  Serial.printf("station_id: %d.\n", station_id);

  http.end();
  return true;
}

bool setup_am2320_sensor()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

  const int num_magnitudes = 2;

  // Prepare JSON document
  const size_t capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(num_magnitudes) + num_magnitudes * JSON_OBJECT_SIZE(3);
  DynamicJsonDocument am2320_json(capacity + 200);
  const size_t response_capacity = JSON_OBJECT_SIZE(3) + num_magnitudes * JSON_ARRAY_SIZE(2) + num_magnitudes * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument am2320_json_response(response_capacity + 200);

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

  // Serialize JSON document
  String am2320_data;
  serializeJson(am2320_json, am2320_data);

  // post data, if the response is 201 then it was created
  // If it was 200 then it was already there
  int post_httpCode;

  http.begin(client, server, port, sensors_endpoint);
  http.addHeader("Content-Type", "application/json");
  const char *headerNames[] = {"Location"};
  http.collectHeaders(headerNames, sizeof(headerNames) / sizeof(headerNames[0]));

  post_httpCode = http.POST(am2320_data); //Send the request
  Serial.printf("POST HTTP code: %d.\n", post_httpCode);
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

  am2320_sensor_id = http.header("Location").toInt();

  response = http.getString(); //Get the response payload
  http.end();
  deserializeJson(am2320_json_response, response);
  Serial.printf("Station response: %s.\n", response.c_str());
  // Get station, sensors and magnitudes ids
  JsonObject am2320_out_mag1 = am2320_json_response["magnitudes"][0];
  am2320_temp_id = am2320_out_mag1["id"];
  JsonObject am2320_out_mag2 = am2320_json_response["magnitudes"][1];
  am2320_hum_id = am2320_out_mag2["id"];
  Serial.printf("am2320_sensor_id: %d, am2320_temp_id: %d, am2320_hum_id: %d.\n",
                am2320_sensor_id, am2320_temp_id, am2320_hum_id);

  am2320.begin();
  delay(500);

  return true;
}

bool delete_extra_sensors()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

  const int num_magnitudes = 2;

  // Prepare JSON document
  const size_t response_capacity = JSON_OBJECT_SIZE(3) + num_magnitudes * JSON_ARRAY_SIZE(2) + num_magnitudes * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument sensors_json_response(response_capacity + 200);

  // post data, if the response is 201 then it was created
  // If it was 200 then it was already there
  int get_httpCode;

  http.begin(client, server, port, sensors_endpoint);
  http.addHeader("Content-Type", "application/json");
  const char *headerNames[] = {"Location"};
  http.collectHeaders(headerNames, sizeof(headerNames) / sizeof(headerNames[0]));

  get_httpCode = http.GET(); //Send the request
  Serial.printf("GET HTTP code: %d.\n", get_httpCode);
  switch (get_httpCode)
  {
  case HTTP_CODE_OK: // Station already existed
    break;
  default:
    http.end();
    return false;
  }

  response = http.getString(); //Get the response payload
  http.end();
  deserializeJson(sensors_json_response, response);
  Serial.printf("Station response: %s.\n", response.c_str());

  JsonArray sensors = sensors_json_response.as<JsonArray>();
  bool to_be_deleted = true;
  for (JsonObject sensor : sensors)
  {
    const int sensor_id = sensor["id"];
    // if sensor[id] is not one of the sensors we setup, delete it
    for (int good_sensor_id : sensor_ids)
    {
      if (sensor_id == good_sensor_id)
      {
        to_be_deleted = false;
      }
    }
    if (to_be_deleted)
    {
      // delete sensor_id
    }
  }
}

void setup_sensors()
{
  // setup AM2320 sensor
  setup_am2320_sensor();

  // Collect all sensor_ids
  sensor_ids[0] = am2320_sensor_id;

  // Delete all other sensors in this station
  delete_extra_sensors();
}

////// Measurement functions
void measure_am2320_sensor()
{
  Serial.println("Measuring AM2320...");
  int conversion_ret_val;
  time_t now = UTC.now();
  // sensor
  humidity = am2320.readHumidity();
  temperature = am2320.readTemperature();

  if (isnan(humidity))
  {
    Serial.println("  Error reading humidity.");
  }
  else
  {
    SensorData humidity_data = {now, am2320_hum_id};
    conversion_ret_val = snprintf(humidity_data.value, sizeof(humidity_data.value), "%.3f", humidity);
    if (conversion_ret_val > 0)
    {
      Serial.printf("  Humidity: %.2f %%.\n", humidity);
      sensor_buffer.push(humidity_data);
    }
    else
    {
      Serial.printf("  Problem converting humidity (%.2f %%) to char[].\n", humidity);
    }
  }

  if (isnan(temperature))
  {
    Serial.println("  Error reading temperature.");
  }
  else
  {
    SensorData temperature_data = {now, am2320_hum_id};
    conversion_ret_val = snprintf(temperature_data.value, sizeof(temperature_data.value), "%.3f", temperature);
    if (conversion_ret_val > 0)
    {
      Serial.printf("  Temperature: %.2f C.\n", temperature);
      sensor_buffer.push(temperature_data);
    }
    else
    {
      Serial.printf("  Problem converting temperature (%.2f C) to char[].\n", temperature);
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
    Serial.println("  post_measurement HTTP Error code: " + http.errorToString(httpCode));
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
  Serial.printf("Sending %d measurements...\n", num_measurements);

  // Prepare JSON document
  const size_t capacity = JSON_ARRAY_SIZE(num_measurements) + num_measurements * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument list_measurement(capacity + 200 * num_measurements);

  for (index_t i = 0; i < num_measurements; i++)
  {
    sensor_data = sensor_buffer[i];
    JsonObject data_0 = list_measurement.createNestedObject();
    data_0["sensor_id"] = am2320_sensor_id;
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
    Serial.println("  Data sent successfully.");
    sensor_buffer.clear();
  }
  else
  {
    Serial.println("  Data was not sent.");
  }
}

void setup()
{
  Serial.begin(115200);

  connect_to_wifi();

  connect_to_time();

  setup_sensors();

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

  // Timer
  measurement_timer.start();
  send_timer.start();
}

void loop()
{
  // Update time if needed
  events();

  // Update timer
  measurement_timer.update();
  send_timer.update();
}