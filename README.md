# home_sensor

## web_client

Vue.js app to display the data collected by the rest_server from the embedded SensorClients.

## rest_server

Gets data from the SensorClients and is used by the web_client to display sensor data.

## SensorClient

Code deployed to the ESP8266 stations.
Deploy with PlatformIO or Arduino. They connect and send data to the rest_server.

## SensorServer

Old code to run a webserver from a ESP8266.
