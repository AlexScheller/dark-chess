FROM python:3.7-alpine

RUN adduser -D u_dark_chess_backend

WORKDIR /home/dark_chess_backend

# Postgres
# RUN apk add --no-cache postgresql-dev
# RUN apk add --no-cache --virtual .build-deps \
# 			python3-dev \
# 			zeromq-dev \
# 			py-gevent \
# 			musl-dev \
# 			gcc

# MySQL
RUN apk add --no-cache mariadb-dev
RUN apk add --no-cache --virtual .build-deps \
			mariadb-dev \
			gcc \
			musl-dev

COPY requirements.txt requirements.txt
# Possibly bad practice
COPY .env .env
RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install -r requirements.txt
# Temporarily (As of 2019-11-10) install a specific version, as v20 has broken
# alpine-linux
RUN venv/bin/pip install 'gunicorn==19.9.0'

RUN apk del .build-deps

COPY dark_chess_api dark_chess_api
COPY migrations migrations
COPY dark_chess_backend.py config.py ./

ENV FLASK_APP dark_chess_backend.py

RUN chown -R u_dark_chess_backend:u_dark_chess_backend ./
USER u_dark_chess_backend

EXPOSE 5000
