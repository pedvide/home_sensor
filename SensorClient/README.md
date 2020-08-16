# SensorClient

Arduino code deployed to each ESP8266 sensor stations.
Each station is made of one or more sensors which contain one or more magnitudes.

The stations connect and send data to the rest_server.

## Deployment

Add a `config.h` file in the `include/` folder with the following data:

```cpp
#ifndef STASSID
#define STASSID "WIFI ID"
#define STAPSK "WIFI PASSWORD"
#endif

#define SERVER_HOSTNAME "hostname of the rest_server"

#define LOCATION "location of this station, change for each station!"
```

Install platformIO or Arduino. Install the ESP8266 extension.

Upload the code and move to final location.
