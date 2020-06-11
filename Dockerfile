FROM python:3.8.3-alpine

ENV API_SERVER=localhost
ENV LOCAL_PORT=20080

RUN apk add --no-cache -t DEPS gcc musl-dev libffi-dev build-base

WORKDIR /ws_flask
ADD requirements.txt ./
ADD deps/ deps/
RUN pip install --no-index --find-links=./deps -r requirements.txt

RUN apk del DEPS

COPY ./ ./

RUN flask init-db
ENTRYPOINT gunicorn --workers=2 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm -b 127.0.0.1:20080 -k flask_sockets.worker app:app
