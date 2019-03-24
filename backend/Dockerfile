FROM python:3.7-alpine

RUN adduser -D u_dark_chess_backend

WORKDIR /home/dark_chess_backend

# RUN apk add --no-cache mariadb-dev
# RUN apk add --no-cache --virtual .build-deps \
# 			mariadb-dev \
# 			gcc \
# 			musl-dev

COPY requirements.txt requirements.txt
# COPY .env .env
RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

# RUN apk del .build-deps

COPY dark_chess_api dark_chess_api
COPY migrations migrations
COPY dark_chess_backend.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP dark_chess_backend.py

RUN chown -R u_dark_chess_backend:u_dark_chess_backend ./
USER u_dark_chess_backend

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]