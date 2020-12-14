from uuid import UUID

from flask import g, jsonify, request, current_app

from dark_chess_api import db, endpointer
from dark_chess_api.modules.users import users
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.errors.handlers import error_response
from dark_chess_api.modules.users.auth import (
	basic_auth, token_auth, check_and_assign_beta_code
)

@endpointer.route('/auth/token', methods=['GET'], bp=users,
	responds={
		200: { 'token': '<token>', 'user': User.mock_dict() },
		404: None
	},
	auth='basic'
)
@basic_auth.login_required
def aquire_token():
	token = g.current_user.get_token()
	db.session.commit()
	return {
		'token' : token,
		'user' : g.current_user.as_dict()
	}

@endpointer.route('/<int:id>', methods=['GET'], bp=users,
	responds={
		200: { 'user': User.mock_dict() },
		404: None
	},
	auth='token (bearer)'
)
@token_auth.login_required
def user_info(id):
	u = User.query.get_or_404(id)
	return u.as_dict()

@endpointer.route('/all', methods=['GET'], bp=users,
	responds={
		200: ['...', User.mock_dict(), '...']
	},
	auth='token (bearer)'
)
@token_auth.login_required
def user_list():
	us = User.query.all()
	return jsonify([u.as_dict() for u in us])

@endpointer.route('/search', methods=['POST'], bp=users,
	accepts={
		'username': { 'type': 'string' }
	},
	responds={
		200: ['...', User.mock_dict(), '...']
	},
	auth='token (bearer)'
)
@token_auth.login_required
def user_search(username):
	us = User.query.filter(User.username.ilike(f'%{username}%')).all()
	return jsonify([u.as_dict() for u in us])

# Currently this requires a beta code. Once that period is over, this code
# should be removed.
@endpointer.route('/auth/register', methods=['POST'], bp=users,
	accepts={
		'username': { 'type': 'string' },
		'email': { 'type': 'string', 'format': 'email' },
		'password': { 'type': 'string' },
		'password_confirmed': { 'type': 'string' }
	},
	responds={
		200: { 'message' : 'Successfully registered user', 'user': User.mock_dict() },
		404: None,
		422: { 'message' : 'Passwords do not match' }
	},
	description='Register a new user'
)
def register_user(username, email, password, password_confirmed):
	# Note: emails are blindly accepted, no assumption is even made that the
	# frontend validated them. Emails are validated with the confirmation
	# pattern rather than some attempt at a regex or something.
	u_check = User.query.filter_by(username=username).first()
	if u_check is not None:
		return error_response(409, 'Username in use')
	u_check = User.query.filter_by(email=email).first()
	if u_check is not None:
		return error_response(409, 'Email is use')
	if password != password_confirmed:
		return error_response(422, 'Passwords do not match')
	new_user = User(username=username, email=email, password=password)
	db.session.add(new_user)
	# BetaCode specific. Because the requirement to use beta codes is switched
	# with a config param, the validation must occur in this route, rather than
	# at the JSON schema level.
	registration_json = request.get_json()
	if current_app.config['BETA_KEYS_REQUIRED']:
		if 'beta_code' not in registration_json:
			db.session.rollback()
			return error_response(400, 'Beta codes are currently required for registration')
		beta_code = registration_json['beta_code']
		if not check_and_assign_beta_code(beta_code, new_user):
			db.session.rollback()
			return error_response(422, 'Invalid beta code')
	db.session.commit()
	return {
		'message' : 'Successfully registered user',
		'user' : new_user.as_dict()
	}

@endpointer.route('/<int:id>/auth/change-password', methods=['PATCH'], bp=users,
	accepts={
		'current_password': { 'type': 'string' },
		'new_password': { 'type': 'string'}
	},
	responds={
		200: { 'message': 'Successfully changed password', 'user': User.mock_dict() },
		403: { 'message': 'Current password incorrect' },
		404: None
	},
	auth='token (bearer)'
)
@token_auth.login_required
def change_password(id, current_password, new_password):
	u = User.query.get_or_404(id)
	if not u.check_password(current_password):
		return error_response(403, 'Current password incorrect')
	u.set_password(new_password)
	db.session.commit()
	return {
		'message' : 'Successfully changed password',
		'user' : u.as_dict()
	}

@endpointer.route('/<int:id>/friend-invite', methods=['POST'], bp=users,
	responds={
		200: { 'message': 'Successfully invited user to be your friend', 'user': User.mock_dict() },
		201: { 'message': 'User already invited to be your friend', 'user': User.mock_dict() },
		403: { 'message': 'Current password incorrect' },
		404: None
	},
	auth='token (bearer)',
	description='Invite a user to be the requesting user\'s friend'
)
@token_auth.login_required
def invite_friend(id):
	u = User.query.get_or_404(id)
	if u in g.current_user.friends_invited:
		return {
			'message': 'User already invited to be your friend',
			'user': u.as_dict()
		}, 201
	g.current_user.invite_friend(u)
	db.session.commit()
	return {
		'message': 'Successfully invited user to be your friend',
		'user': u.as_dict()
	}

@endpointer.route('/<int:id>/accept-friend-invite', methods=['PATCH'], bp=users,
	responds={
		200: { 'message': 'Successfully accepted friend invite', 'user': User.mock_dict() },
		201: { 'message': 'You are already friends with this user', 'user': User.mock_dict() },
		400: { 'message': 'You don\'t have a friend invite from this player' },
		404: None
	},
	auth='token (bearer)'
)
@token_auth.login_required
def accept_friend_invite(id):
	u = User.query.get_or_404(id)
	if u not in g.current_user.friend_invites:
		return error_response(400, 'You don\'t have a friend invite from this player')
	if u in g.current_user.friends:
		return {
			'message': 'You are already friends with this user',
			'user': u.as_dict()
		}, 201
	g.current_user.accept_friend(u)
	db.session.commit()
	return {
		'message': 'Successfully accepted friend invite',
		'user': u.as_dict()
	}
