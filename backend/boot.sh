#!/bin/sh
# For usage with docker
source venv/bin/activate
flask db upgrade
exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - dark_chess_backend:app
