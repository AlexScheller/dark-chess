FROM python:3.8-slim-buster

RUN adduser --disabled-password --gecos "" u_dark_chess_backend

WORKDIR /home/dark_chess_backend

COPY requirements.txt requirements.txt

# Copying the python .env, not a docker .env, possibly bad practice.
COPY .env .env

RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install -r requirements.txt

RUN venv/bin/pip install gunicorn


COPY dark_chess_api dark_chess_api
COPY migrations migrations
COPY dark_chess_backend.py config.py ./

ENV FLASK_APP dark_chess_backend.py

RUN chown -R u_dark_chess_backend:u_dark_chess_backend ./
USER u_dark_chess_backend

EXPOSE 5000
