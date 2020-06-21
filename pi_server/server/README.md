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
