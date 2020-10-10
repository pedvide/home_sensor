# InfluxDB

Avoid having to use sudo all the time with docker:
`sudo usermod -aG docker pedvide`

## Create user, settings, and folders

```bash
sudo useradd -rs /bin/false influxdb
sudo mkdir -p /var/lib/influxdb
sudo chown influxdb:influxdb /var/lib/influxdb/
```

## Create admin account

```bash
docker run --rm -e INFLUXDB_HTTP_AUTH_ENABLED=true \
	-e INFLUXDB_ADMIN_USER=influx_admin -e INFLUXDB_ADMIN_PASSWORD=influx_admin123 \
	-v /var/lib/influxdb:/var/lib/influxdb \
	influxdb /init-influxdb.sh
```

## Create network

`docker network create influxdb`

## Run container

```bash
docker run -d -p 8086:8086 --net influxdb \
 --user "$(id -u influxdb)":"$(id -g influxdb)" --name=influxdb \
 --restart=always \
 -v /var/lib/influxdb:/var/lib/influxdb \
 -e INFLUXDB_REPORTING_DISABLED=true \
 -e INFLUXDB_HTTP_AUTH_ENABLED=true \
 influxdb
```

## Test

Test the database:

```bash
curl -G -u influx_admin:influx_admin123 http://localhost:8086/query --data-urlencode "q=SHOW DATABASES" | jq
```

# Telegraf

## Create user, settings, and folders

```bash
sudo useradd -rs /bin/false telegraf
sudo mkdir -p /etc/telegraf
docker run --rm telegraf telegraf config | sudo tee /etc/telegraf/telegraf.conf > /dev/null
sudo chown telegraf:telegraf /etc/telegraf/*
```

Edit the telegraf config file:

```
sudo vim /etc/telegraf/telegraf.conf
```

In the section [[outputs.influxdb]], change "HTTP Basic Auth" to:

```
username = "telegraf"
password = "telegraf123"
```

And change url to

```
urls = ["http://influxdb:8086"]
```

In the [agent] section change hostname:

```
hostname = "$HOST_HOSTNAME"
```

### Docker monitoring

`sudo usermod -aG docker telegraf`

Uncomment the [[inputs.docker]]
and the endpoint setting.

### CPU temp and net monitoring

Uncomment [[inputs.sensors]], and [[inputs.net]] and `sudo apt install lm-sensors`.

## Create database and user on influxdb

```bash
curl -POST -u influx_admin:influx_admin123 http://localhost:8086/query \
--data-urlencode "q=CREATE DATABASE telegraf WITH DURATION 30d SHARD DURATION 1d NAME "monthly"; CREATE USER "telegraf" WITH PASSWORD 'telegraf123'; GRANT ALL ON "telegraf" TO "telegraf""
```

## Run container

Use the docker gid to be able to access the docker socket

```bash
docker run -d --user "$(id -u telegraf)":"$(getent group docker | cut -d: -f3)" --name=telegraf \
 --net influxdb --restart=always \
 -e HOST_HOSTNAME=`hostname` \
 -e HOST_MOUNT_PREFIX=/hostfs -v /:/hostfs:ro \
 -e HOST_PROC=/hostfs/proc  \
 -e HOST_SYS=/hostfs/sys \
 -e HOST_VAR=/hostfs/var \
 -v /var/run/docker.sock:/var/run/docker.sock \
 -v /etc/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro \
 telegraf
```

## Test

```bash
curl -G -u influx_admin:influx_admin123 http://localhost:8086/query
	--data-urlencode "q=SELECT * FROM telegraf.autogen.cpu LIMIT 1" | jq
```

# Grafana

## Setup

```bash
sudo useradd -rs /bin/false grafana
sudo mkdir -p /var/lib/grafana
sudo chown grafana:grafana /var/lib/grafana
```

## Run container

```bash
docker run -d --name=grafana -p 3000:3000 --net influxdb \
--restart=always \
 -v "/var/lib/grafana/:/var/lib/grafana" \
 -e GF_DISABLE_INITIAL_ADMIN_CREATION=true \
 -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=grafana123 \
 -e GF_DATE_FORMATS_INTERVAL_DAY='DD/MM' -e GF_DATE_FORMATS_INTERVAL_HOUR='DD/MM HH:mm' \
 --user "$(id -u grafana)":"$(id -g grafana)" \
 grafana/grafana
```

## Setup

Go to hostname:3000.

Use admin:grafana123 to log in.

```bash
curl -d '{
"name": "InfluxDB_telegraf",
"type": "influxdb",
"access": "proxy",
"url": "http://influxdb:8086",
"basicAuth": true,
"basicAuthUser": "influx_admin",
"secureJsonData": {
"basicAuthPassword": "influx_admin123"
},
"database": "telegraf",
"user": "telegraf",
"password": "telegraf123",
}' http://admin:grafana123@localhost:3000/api/datasources
```

Add a new data source of type Influxdb, set the URL as "http://influxdb:8086".

Add the influxdb username and passwords (influx_admin, influx_admin123) and the database: telegraf, with credentials telegraf and telegraf123.
