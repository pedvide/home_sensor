FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

ENV MODULE_NAME="rest_server.app"
ENV VARIABLE_NAME="app"
ENV PORT 80

COPY ./requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY ./rest_server ./rest_server

EXPOSE 80
USER nobody
