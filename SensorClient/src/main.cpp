
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

//// Main server
const char *server = SERVER_HOSTNAME;
const char *api_endpoint = "/api/upload_data";
const uint8_t port = 80;

//// Time
Timezone Amsterdam;

///// Common sensor
const uint32_t sensor_period_s = 5;
void measure_sensors();
Ticker measurement_timer(measure_sensors, sensor_period_s * 1e3, 0, MILLIS);
// AM2320 Sensor
const char *sensor_am2320_id = "AM2320";
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
int httpCode;
String response;
// String postData;
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

bool post_request(String &data)
{
  // Post Data
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_to_wifi();
    return false;
  }

  http.begin(client, server, port, api_endpoint);
  http.addHeader("Content-Type", "application/json");

  httpCode = http.POST(data); //Send the request
  if (httpCode > 0)
  {
    response = http.getString(); //Get the response payload
    response.trim();
    response.replace("\n", "");
    Serial.printf("HTTP code: %d. Response: %s.\n", httpCode, response.c_str());
    if (httpCode == HTTP_CODE_OK)
    {
      http.end();
      return true;
    }
  }
  else
  {
    Serial.printf("HTTP Error code: %d.\n", httpCode); //Print HTTP return code and response
  }
  http.end();
  return false;
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
  StaticJsonDocument<400> doc;
  doc["station_id"] = mac_sha;
  doc["sensor_id"] = sensor_am2320_id;
  doc["time"] = sensor_data.epoch;

  JsonArray data = doc.createNestedArray("data");

  JsonObject data_0 = data.createNestedObject();
  data_0["name"] = "temperature";
  data_0["unit"] = "C";
  data_0["value"] = isnan(sensor_data.temperature) ? (char *)0 : String(sensor_data.temperature);

  JsonObject data_1 = data.createNestedObject();
  data_1["name"] = "humidity";
  data_1["unit"] = "%";
  data_1["value"] = isnan(sensor_data.humidity) ? (char *)0 : String(sensor_data.humidity);

  // Serialize JSON document
  String post_data;
  serializeJson(doc, post_data);

  bool success = post_request(post_data);

  if (success)
  {
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