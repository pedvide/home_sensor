# SensorClient

Arduino code deployed to each ESP8266 sensor stations.
Each station is made of one or more sensors which contain one or more magnitudes.

The stations connect and send data to the rest_server.

## Deployment

Change the values in the `include/config.h.example` file to your settings and save it without the `.example` extension.

Install platformIO or Arduino. Install the ESP8266 extension.

Upload the code and move to final location.
