
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
String station_endpoint;
uint8_t station_id;
const uint8_t port = 80;

//// Time
Timezone Amsterdam;

///// Common sensor
const uint32_t sensor_period_s = 10;
void measure_sensors();
Ticker measurement_timer(measure_sensors, sensor_period_s * 1e3, 0, MILLIS);

// AM2320 Sensor
uint8_t am2320_sensor_id, am2320_temp_id, am2320_hum_id;
const char *sensor_am2320_name = "AM2320";
typedef struct
{
  time_t epoch;
  float temperature;
  float humidity;
} SensorAM2320Data;
SensorAM2320Data sensor_data;
float temperature, humidity;
CircularBuffer<SensorAM2320Data, 255> sensor_am2320_buffer; // Keep some raw data
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
  const size_t capacity = JSON_ARRAY_SIZE(1) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(2) + 3 * JSON_OBJECT_SIZE(3);
  DynamicJsonDocument station_json(capacity + 200);
  const size_t response_capacity = JSON_ARRAY_SIZE(1) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(3) + 3 * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument station_json_response(response_capacity + 200);

  station_json["token"] = mac_sha;
  station_json["location"] = location;
  JsonArray sensors_in = station_json.createNestedArray("sensors");

  JsonObject sensor1_in = sensors_in.createNestedObject();
  sensor1_in["name"] = sensor_am2320_name;
  JsonArray sensor_1_in_magnitudes = sensor1_in.createNestedArray("magnitudes");

  JsonObject mag1_in = sensor_1_in_magnitudes.createNestedObject();
  mag1_in["name"] = "temperature";
  mag1_in["unit"] = "C";
  mag1_in["precision"] = 0.1;

  JsonObject mag2_in = sensor_1_in_magnitudes.createNestedObject();
  mag2_in["name"] = "humidity";
  mag2_in["unit"] = "%";
  mag2_in["precision"] = 0.1;

  // Serialize JSON document
  String station_data;
  serializeJson(station_json, station_data);

  // First post data, if the response is 201 then it was created
  // If it was 200 then it was already there,
  // send again as PUT to update
  int post_httpCode, put_httpCode, get_httpCode;

  http.begin(client, server, port, stations_endpoint);
  http.addHeader("Content-Type", "application/json");
  const char *headerNames[] = {"Location"};
  http.collectHeaders(headerNames, sizeof(headerNames) / sizeof(headerNames[0]));

  post_httpCode = http.POST(station_data); //Send the request
  Serial.printf("POST HTTP code: %d.\n", post_httpCode);
  switch (post_httpCode)
  {
  case HTTP_CODE_OK: // Station already existed
    // PUT and then GET the station to update location/sensors/etc.
    station_id = http.header("Location").toInt();
    station_endpoint = String(stations_endpoint) + "/" + station_id;
    http.end();
    http.begin(client, server, port, station_endpoint);
    http.addHeader("Content-Type", "application/json");
    put_httpCode = http.PUT(station_data); //Send the request
    Serial.printf("PUT HTTP code: %d.\n", put_httpCode);
    switch (put_httpCode)
    {
    case HTTP_CODE_NO_CONTENT: // PUT succesful
      http.end();
      http.begin(client, server, port, station_endpoint);
      http.addHeader("Content-Type", "application/json");
      get_httpCode = http.GET(); //Send the request
      Serial.printf("GET HTTP code: %d.\n", get_httpCode);
      switch (get_httpCode)
      {
      case HTTP_CODE_OK: // Got the station
        break;
      default:
        http.end();
        return false;
      }
      break;
    default:
      http.end();
      return false;
    }
    break;
  case HTTP_CODE_CREATED: // Station created
    break;
  default:
    http.end();
    return false;
  }

  response = http.getString(); //Get the response payload
  deserializeJson(station_json_response, response);
  Serial.printf("Station response: %s.\n", response.c_str());
  // Get station, sensors and magnitudes ids
  station_id = station_json_response["id"];
  JsonObject sensor1_out = station_json_response["sensors"][0];
  am2320_sensor_id = sensor1_out["id"];
  JsonObject sensor1_out_mag1 = sensor1_out["magnitudes"][0];
  am2320_temp_id = sensor1_out_mag1["id"];
  JsonObject sensor1_out_mag2 = sensor1_out["magnitudes"][1];
  am2320_hum_id = sensor1_out_mag2["id"];
  Serial.printf("station_id: %d, am2320_sensor_id: %d, am2320_temp_id: %d, am2320_hum_id: %d.\n",
                station_id, am2320_sensor_id, am2320_temp_id, am2320_hum_id);

  http.end();
  return true;
}

void setup_sensors()
{
  am2320.begin();
  delay(500);
}

////// Measurement functions

void measure_am2320_sensor()
{
  // sensor
  humidity = am2320.readHumidity();
  if (isnan(humidity))
  {
    Serial.println("Error reading humidity.");
  }
  temperature = am2320.readTemperature();
  if (isnan(temperature))
  {
    Serial.println("Error reading temperature.");
  }
  if (isnan(temperature) && isnan(humidity))
  {
    // All datapoints are invalid
    return;
  }
  sensor_am2320_buffer.push(SensorAM2320Data{UTC.now(), temperature, humidity});
  Serial.printf("Sensor values: %.2f C, %.2f %%.\n", temperature, humidity);
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
    Serial.println("post_measurement HTTP Error code: " + http.errorToString(httpCode));

    return false;
  }
}

void send_am2320_data()
{
  if (sensor_am2320_buffer.isEmpty())
  {
    return;
  }

  // Attempt to send data
  sensor_data = sensor_am2320_buffer.last();

  // Prepare JSON document
  const size_t capacity = JSON_ARRAY_SIZE(2) + 2 * JSON_OBJECT_SIZE(4);
  DynamicJsonDocument list_measurement(capacity + 200);

  JsonObject data_0 = list_measurement.createNestedObject();
  data_0["sensor_id"] = am2320_sensor_id;
  data_0["magnitude_id"] = am2320_temp_id;
  data_0["timestamp"] = sensor_data.epoch;
  data_0["value"] = isnan(sensor_data.temperature) ? (char *)0 : String(sensor_data.temperature);

  JsonObject data_1 = list_measurement.createNestedObject();
  data_1["sensor_id"] = am2320_sensor_id;
  data_1["magnitude_id"] = am2320_hum_id;
  data_1["timestamp"] = sensor_data.epoch;
  data_1["value"] = isnan(sensor_data.humidity) ? (char *)0 : String(sensor_data.humidity);

  // Serialize JSON document
  String post_data;
  serializeJson(list_measurement, post_data);

  bool success = post_measurement(post_data, station_endpoint + "/measurements");

  if (success)
  {
    Serial.println("Data sent successfully.");
    sensor_am2320_buffer.pop();
  }
}

void send_data()
{
  send_am2320_data();
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

  // send_data();

  // if ((millis() % 5000) == 0) {
  //   Serial.println("Begin of buffer.");
  //   while (!sensor_buffer.isEmpty()) {
  //     SensorData data;
  //     data = sensor_buffer.pop();
  //     Serial.printf("[%s], T = %.2f C, H = %.1f %%.\n",
  //       Amsterdam.dateTime(data.epoch).c_str(), data.temperature, data.humidity);
  //   }
  //   Serial.println("End of buffer.");
  // }
}