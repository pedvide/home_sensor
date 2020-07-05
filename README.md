# home_sensor

Services for a smart home.

## web_client

Vue.js app to display the data collected by the rest_server from the embedded SensorClients.

## rest_server

Python REST API using FastAPI and SQLAlchemy (SQLite).

Gets data from the SensorClients and is used by the web_client to display sensor data.

## SensorClient

Aruidno code deployed to the ESP8266 sensor stations.
Deploy with PlatformIO or Arduino. They connect and send data to the rest_server.

## SensorServer

Old code to run a webserver from a ESP8266.
