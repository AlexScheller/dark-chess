# The following auth code is taken almost verbatim from "microblog",
# (see README.md)

from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.errors.handlers import error_response

basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
	user = User.query.filter_by(username=username).first()
	if user is None:
		return False
	g.current_user = user
	return user.check_password(password)

token_auth = HTTPTokenAuth()

@token_auth.verify_token
def verify_token(token):
	g.current_user = User.get_with_token(token) if token else None
	return g.current_user is not None

@token_auth.error_handler
def token_auth_error():
	return error_response(401)