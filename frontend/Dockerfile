FROM python:3.8-slim-buster

RUN adduser --disabled-password --gecos "" u_dark_chess_frontend

WORKDIR /home/dark_chess_frontend

COPY requirements.txt requirements.txt
# Copying the python .env, not a docker .env, possibly bad practice.
COPY .env .env

RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt

RUN venv/bin/pip install gunicorn

COPY dark_chess_app dark_chess_app
COPY dark_chess_frontend.py config.py ./

ENV FLASK_APP dark_chess_frontend.py

RUN chown -R u_dark_chess_frontend:u_dark_chess_frontend ./
USER u_dark_chess_frontend

EXPOSE 5005