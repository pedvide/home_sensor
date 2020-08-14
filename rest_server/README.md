# rest_Server

## Deployment

Install packages in requirements.txt

### Deploy rest_server

Copy server folder with rsync.

### Deploy backend with systemd module

Create socket with `sudo vim /etc/systemd/system/home_sensor_backend.socket`:

```
[Unit]
Description=home-sensor backend socket

[Socket]
ListenStream=/run/home_sensor_backend.sock

[Install]
WantedBy=sockets.target
```

Start it with

```bash
$ sudo systemctl start home_sensor_backend.socket
$ sudo systemctl enable home_sensor_backend.socket
```

Create service with `sudo vim /etc/systemd/system/home_sensor_backend.service`

```
[Unit]
Description=home-sensor backend daemon
Requires=home_sensor_backend.socket
After=network.target

[Service]
User=pedvide
Group=www-data
WorkingDirectory=/home/pedvide/home_sensor/rest_server
ExecStart=/home/pedvide/home_sensor/rest_server/env/bin/gunicorn \
          --access-logfile /var/log/home_sensor_backend/access.log \
          --error-logfile /var/log/home_sensor_backend/error.log \
          --workers 1 \
          --bind unix:/run/home_sensor_backend.sock \
          -k uvicorn.workers.UvicornWorker \
          --name home_sensor_backend \
          rest_server.app:app

[Install]
WantedBy=multi-user.target
```

Start it with

```bash
$ sudo systemctl start home_sensor_backend
$ sudo systemctl enable home_sensor_backend
```

Test that it works with, you should see html.

```
$ curl --unix-socket /run/home_sensor_backend.sock localhost/api/docs
```

### Configure reverse proxy

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

Nginx (both web_client and backend rest_server):

```
$ sudo tail /var/log/nginx/access.log
$ sudo tail /var/log/nginx/error.log
```

Only backend service:

```
$ sudo tail /var/log/home_sensor_backend/access.log
$ sudo tail /var/log/home_sensor_backend/error.log
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
