# client

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

## Deployment for raspberry pi

Install nginx and edit the conf file with

```bash
sudo vim /etc/nginx/sites-enabled/default
```

```
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        root /home/pedvide/home_sensor/client/dist;
        index index.html index.htm;
        location / {
                # First attempt to serve request as file, then
                # as directory, then index.html then fall back to displaying a 404.
                try_files $uri $uri/ /index.html =404;
        }
}
```

Build with `npm run build` and use rsync to copy dist folder to `/home/pedvide/home_sensor/client/dist`.

Start nginx service:

```bash
sudo systemctl start nginx.service
```

Go to `<hostname>` to see web app.
