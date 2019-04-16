from flask_socketio import emit
from dark_chess_app import socketio

@socketio.on('connect')
def handle_connect():
	print('Client connected.')