FROM python:3.7-alpine

RUN adduser -D u_dark_chess_frontend

WORKDIR /home/dark_chess_frontend

# RUN apk add --no-cache postgresql-dev
# RUN apk add --no-cache --virtual .build-deps \
# 			python3-dev \
# 			zeromq-dev \
# 			py-gevent \
# 			musl-dev \
# 			gcc

COPY requirements.txt requirements.txt
# Possibly bad practice
COPY .env .env
RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

# RUN apk del .build-deps

COPY dark_chess_app dark_chess_app
COPY dark_chess_frontend.py config.py ./

ENV FLASK_APP dark_chess_frontend.py

RUN chown -R u_dark_chess_frontend:u_dark_chess_frontend ./
USER u_dark_chess_frontend

EXPOSE 5005