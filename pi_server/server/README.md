# server

## Deployment for raspberry pi

run locally

```
uvicorn server.app:app --reload -port 8080
```

Run in the pi with

```
uvicorn server.app:app --reload --port 8080 --host 0.0.0.0
```

or

```
gunicorn -k uvicorn.workers.UvicornWorker server.app:app --reload --bind 0.0.0.0:8080 -w 2 --access-logfile -
```
