from flask import g, current_app
from flask_socketio import emit
from dark_chess_api import socketio
from dark_chess_api.modules.websockets.connection_handler import (
	token_auth_required
)

@socketio.on('connect', namespace='/match-moves')
def handle_connect():
	if current_app.config['DEBUG']:
		print('Client connection event.')
	# if current_user.is_authenticated:
	# emit('connection accepted', {
	# 	'msg': f'user ({g.current_user.username}:{g.current_user.id}) accepted'
	# })
	# else:
		# return False

@socketio.on('authenticate', namespace='/match-moves')
@token_auth_required
def handle_authenticate(json):
	if current_app.config['DEBUG']:
		print('Client successfully authenticated')
	emit('authenticated', {
		'msg': f'user ({g.current_user.username}:{g.current_user.id}) authenticated'
	})

@socketio.on('disconnect', namespace='/match-moves')
def handle_disconnect():
	if current_app.config['DEBUG']:
		print('Client disconnection event.')

@socketio.on('move-request')
@token_auth_required
def handle_move_request(data):
	print(data)