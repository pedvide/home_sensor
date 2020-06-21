# home_sensor

## Deployment

Install packages in requirements.txt

### Deploy server

Copy server folder with rsync.

### Deploy web client

Build with `npm run build` and use rsync to copy `dist` folder to `/home/pedvide/home_sensor/client/dist`.

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
WorkingDirectory=/home/pedvide/home_sensor
ExecStart=/home/pedvide/home_sensor/env/bin/gunicorn \
          --access-logfile /var/log/home_sensor_backend/access.log \
          --error-logfile /var/log/home_sensor_backend/error.log \
          --workers 1 \
          --bind unix:/run/home_sensor_backend.sock \
          -k uvicorn.workers.UvicornWorker \
          --name home_sensor_backend \
          server.app:app

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

nginx configuration:

```
$ cat /etc/nginx/sites-enabled/default
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        root /home/pedvide/home_sensor/client/dist;
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

Nginx (both web frontend and backend server):

```
$ sudo tail /var/log/nginx/access.log
$ sudo tail /var/log/nginx/error.log
```

Only backend service:

```
$ sudo tail /var/log/home_sensor_backend/access.log
$ sudo tail /var/log/home_sensor_backend/error.log
```
