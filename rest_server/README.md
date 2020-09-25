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

Create a influxdb container, with a bridge network called influxdb,
and execute to create a database and user.

```bash
curl -POST -u influx_admin:influx_admin123 http://localhost:8086/query \
--data-urlencode "q=CREATE DATABASE home_sensor; CREATE USER "homesensor" WITH PASSWORD 'homesensor123'; GRANT ALL ON "home_sensor" TO "homesensor""
```

Run container:

```bash
docker run -d --name homesensor -p 80:80 \
  -e MAX_WORKERS=1 \
  --net influxdb \
  -v /home/pedvide/home-sensor/rest_server/sql_app.db:/app/sql_app.db \
  rest_server
```

## Logs

```bash
docker logs homesensor
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
