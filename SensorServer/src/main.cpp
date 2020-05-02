
#include <ESP8266WiFi.h>
#include "ESPAsyncTCP.h"
#include "ESPAsyncWebServer.h"
#include <ezTime.h>
#include "FS.h"

#include "config.h"

//// WiFi
const char* deviceName = SERVER_HOSTNAME;
const char *ssid = STASSID;
const char *password = STAPSK;


//// Time
Timezone Amsterdam;


//// Server
AsyncWebServer server(80);
// Index template
const String index_html;

// Replaces placeholder with DHT values
String processor(const String& var){
  //Serial.println(var);
  if(var == "TEMPERATURE"){
    return String(20);
  }
  else if(var == "HUMIDITY"){
    return String(10);
  }
  else if(var == "SENSOR_ID"){
    return String("Living_room");
  }
  return String();
}


void connect_to_wifi() {
  // Connect to Wi-Fi
  Serial.println("Connecting to WiFi");
  WiFi.disconnect();
  WiFi.mode(WIFI_STA); //WiFi mode station (connect to wifi router only
  WiFi.hostname(deviceName);
  delay(200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();

  // Last checks
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("Fail connecting");
    ESP.restart();
  }
  WiFi.setAutoReconnect(true);

  // Print ESP8266 Local IP Address
  Serial.println("Connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}


void connect_to_time() {
  setDebug(ezDebugLevel_t::INFO);
  waitForSync();
  setInterval(60 * 60); // 1h in seconds

  Serial.println("UTC: " + UTC.dateTime());
	
	Amsterdam.setLocation("Europe/Amsterdam");
	Serial.println("Amsterdam time: " + Amsterdam.dateTime());
}


void setup_server() {
  // Web server
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(SPIFFS, "/index.html", "text/html", false, processor);
  });

  // API server
  server.on("/api/temperature", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", String(20).c_str());
  });
  server.on("/api/humidity", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", String(10).c_str());
  });

  server.on("/api/upload_data", HTTP_POST, [](AsyncWebServerRequest *request){
    if(request->hasParam("id", true) && request->hasParam("epoch", true) 
    && request->hasParam("temperature", true) && request->hasParam("humidity", true)) {
      const String id = request->getParam("id", true)->value();
      const uint32_t epoch = request->getParam("epoch", true)->value().toInt();
      const float temp = request->getParam("temperature", true)->value().toFloat();
      const float hum = request->getParam("humidity", true)->value().toFloat();
      Serial.printf("[%s] id: %s, Temperature: %.2f C, Humidity: %.2f %%\n", 
        Amsterdam.dateTime(epoch, ISO8601).c_str(), id.c_str(), temp, hum);
      request->send(200, "text/plain", "OK");
    } else {
      Serial.println("Wrong POST parameters.");
      request->send(404, "text/plain", "Missing or wrong parameters. Must have 'id', 'temperature', and 'humidity'.");
    }    
  });

  server.on("/api/time", HTTP_GET, [](AsyncWebServerRequest *request){
    uint32_t epoch = 1;
    request->send(200, "text/plain", String(epoch).c_str());
  });

  server.onNotFound([](AsyncWebServerRequest *request){
    Serial.println("404.");
    request->send(404, "text/plain", "Not found");
  });

  // Start server
  server.begin();

}


void setup(){
  // Serial port for debugging purposes
  Serial.begin(115200);

  if (!SPIFFS.begin()) {
      Serial.println("SPIFFS failed");
      ESP.restart();
  }

  // Connect to Wi-Fi
  connect_to_wifi();

  // Connect to time server
  connect_to_time();

  // Setup and start server
  setup_server();
}
 
void loop(){
  // Update time if needed
  events();

}