from flask import g, current_app
from flask_socketio import emit, join_room
from dark_chess_api import socketio
# See the note in `connection_handler.py` concerning this function
# from dark_chess_api.modules.websockets.connection_handler import (
# 	token_auth_required
# )

#####################
#  Incoming Events  #
#####################

@socketio.on('connect', namespace='/match-moves')
def handle_connect():
	if current_app.config['DEBUG']:
		print('Client connection event.')

@socketio.on('authenticate', namespace='/match-moves')
def handle_authenticate(json):
	if current_app.config['DEBUG']:
		print(f'Client successfully authenticated. Connected from match {json["connectionHash"]}')
		print(f'Client joining room: {json["connectionHash"]}')
	join_room(json['connectionHash'])
	# emit('authenticated', {
	# 	'msg': f'user ({g.current_user.username}:{g.current_user.id}) authenticated'
	# })

@socketio.on('disconnect', namespace='/match-moves')
def handle_disconnect():
	if current_app.config['DEBUG']:
		print('Client disconnection event.')

#####################
#  Outgoing Events  #
#####################

def broadcast_move_made(player, move, current_fen, connection_hash):
	print('emitting')
	socketio.emit('move-made', {
			'player': player.as_dict(),
			'current_fen': current_fen,
			'uci_string': move
		},
		room=connection_hash,
		namespace='/match-moves'
	)