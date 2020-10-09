from flask import current_app, g
from functools import wraps
from flask_socketio import disconnect
from dark_chess_api.modules.users.models import User

# Token auth is currently not required while the entire model of api calls from
# the browsers is being reworked. At this point in time, it's seen as ok for
# clients to connect via ws without any form of authentication beyond the match
# connection hash, as the api doesn't accept any input over ws, it only outputs
# events. It's not really a big deal if a malicious user wants to 'listen in'
# on some random game.

# The following method is kept for posterity's sake in case some kind of token
# authentication is indeed required. If that occurs, the token used should NOT
# be the same as the user's api token (i.e. an additional token model/field
# should be created).

# def token_auth_required(func):
# 	@wraps(func)
# 	def decorated(*args, **kwargs):
# 		if not 'token' in args[0]:
# 			if current_app.config['DEBUG']:
# 				print('No token in event json, disconnecting.')
# 			disconnect()
# 		token = args[0]['token']
# 		g.current_user = User.get_with_token(token) if token else None
# 		if g.current_user is None:
# 			if current_app.config['DEBUG']:
# 				print('No user for auth token, disconnecting.')
# 			disconnect()
# 		return func(*args, **kwargs)
# 	return decorated