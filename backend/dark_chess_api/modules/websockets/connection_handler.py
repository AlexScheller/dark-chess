from flask import current_app, g
from functools import wraps
from flask_socketio import disconnect
from dark_chess_api.modules.users.models import User

def token_auth_required(func):
	@wraps(func)
	def decorated(*args, **kwargs):
		if not 'token' in args[0]:
			if current_app.config['DEBUG']:
				print('No token in event json, disconnecting.')
			disconnect()
		token = args[0]['token']
		g.current_user = User.get_with_token(token) if token else None
		if g.current_user is None:
			if current_app.config['DEBUG']:
				print('No user for auth token, disconnecting.')
			disconnect()
		return func(*args, **kwargs)
	return decorated