# rest_server

## Development

### Installation

Create a virtual enviroment and install the packages in requirements:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Testing

```bash
pytest tests/
```

## Deployment with Docker

Build image

```bash
docker build -t rest_server -f docker/Dockerfile .
```

Create a influxdb container, with a bridge network called influxdb, and execute:

```bash
curl -POST -u influx_admin:influx_admin123 http://localhost:8086/query \
--data-urlencode "q=CREATE DATABASE home_sensor; CREATE USER "homesensor" WITH PASSWORD 'homesensor123'; GRANT ALL ON "home_sensor" TO "homesensor""
```

Run container:

```bash
docker run -d --name home_sensor_rest_server -p 80:80 \
  -e MAX_WORKERS=1 \
  --net influxdb \
  -v /home/pedvide/home-sensor/rest_server/sql_app.db:/sql_app.db \
  rest_server
```

### Configure reverse proxy

Install nginx with `sudo apt install nginx`.

nginx configuration (includes web_client config):

```
$ cat /etc/nginx/sites-enabled/default
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        root /home/pedvide/home_sensor/web_client/dist;
        index index.html index.htm;

        # backend rest server
        location /api {
                include proxy_params;
                proxy_pass http://unix:/run/home_sensor_backend.sock;
        }
        # backend rest server docs
        location ~ (/docs|/redoc|/openapi.json) {
                include proxy_params;
                proxy_pass http://unix:/run/home_sensor_backend.sock;
        }

        # ignore errors accesing favicon
        location = /favicon.ico { access_log off; log_not_found off; }

        # front end client app
        location / {
                # First attempt to serve request as file, then
                # as directory, then index.html then fall back to displaying a 404.
                try_files $uri $uri/ /index.html =404;
        }

}
```

Start nginx service:

```bash
$ sudo systemctl start nginx.service
$ sudo systemctl enable nginx.service
```

## Logs

```bash
docker logs home_sensor_rest_server
# docker logs home_sensor_web_client
```

## Copy sqlite to influxdb

```python
import pandas as pd
import sqlite3
con = sqlite3.connect("sql_app.db")
df = pd.read_sql_query("SELECT * from measurements", con)
df = df.set_index(pd.to_datetime(df.timestamp, unit="s"))
df = df.drop(columns=["id", "timestamp"])
df.value = df.value.astype("float")

from influxdb import DataFrameClient
client = DataFrameClient(host='localhost', port=8086, username="homesensor", password="", database="home_sensor")

client.write_points(df, "raw_data", tag_columns=["station_id", "sensor_id", "magnitude_id"], field_columns=["value"], time_precision="s", batch_size=1000)
```
