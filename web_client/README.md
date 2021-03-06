# web_client

## Project setup

```
npm install
```

### Compiles and hot-reloads for development

```
npm run serve
```

### Compiles and minifies for production

```
npm run build
```

### Lints and fixes files

```
npm run lint
```

### Customize configuration

See [Configuration Reference](https://cli.vuejs.org/config/).

## Deployment

### Deployment with docker

Build image:

```bash
docker build -t home-sensor/web -f docker/Dockerfile .
```

Then run with:
```bash
docker run -it -p 8080:8080 --name home-sensor-web home-sensor/web
```

### Deployment for raspberry pi

Install nginx and edit the conf file with

```bash
sudo vim /etc/nginx/sites-enabled/default
```

```
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        root /home/pedvide/home_sensor/web_client/dist;
        index index.html index.htm;
        location / {
                # First attempt to serve request as file, then
                # as directory, then index.html then fall back to displaying a 404.
                try_files $uri $uri/ /index.html =404;
        }
}
```

Build with `npm run build` and use rsync to copy dist folder to `/home/pedvide/home_sensor/web_client/dist`.

Start nginx service:

```bash
sudo systemctl start nginx.service
```

Go to `<hostname>` to see web app.

### Logs

Nginx web_client:

```
$ sudo tail /var/log/nginx/access.log
$ sudo tail /var/log/nginx/error.log
```
