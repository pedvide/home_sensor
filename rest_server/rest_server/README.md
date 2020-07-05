# server

## Deployment for raspberry pi

Copy server folder with rsync.
Test that it runs with

```
$ gunicorn -k uvicorn.workers.UvicornWorker server.app:app --reload --bind 0.0.0.0:8080 -w 1 --access-logfile -
```

Go to `<hostname>:8080/api/docs` to see docs page.
