from flask import g, jsonify, request
from dark_chess_api import db
from dark_chess_api.modules.users import users
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.errors.handlers import error_response
from dark_chess_api.modules.auth.utils import (
	basic_auth, token_auth, check_and_assign_beta_code
)
from dark_chess_api.modules.utilities import validation

@users.route('/auth/token', methods=['GET'])
@basic_auth.login_required
def aquire_token():
	token = g.current_user.get_token()
	db.session.commit()
	return {
		'token' : token,
		'user' : g.current_user.as_dict()
	}

@users.route('/<int:id>', methods=['GET'])
@token_auth.login_required
def user_info(id):
	u = User.query.get_or_404(id)
	return u.as_dict()

# Currently this requires a beta code. Once that period is over, this code
# should be removed.
@users.route('/auth/register', methods=['POST'])
@validation.validate_json_payload
def register_user():
	registration_json = request.get_json()
	new_username = registration_json['username']
	# Note: emails are blindly accepted, no assumption is even
	# made that the frontend validated them. Email validation
	# is a difficult task that I've decided not to bother
	# attempting on the back end, opting instead for the
	# confirmation pattern to ensure valid emails.
	new_email = registration_json['email']
	new_password = registration_json['password']
	u = User.query.filter_by(username=new_username).first()
	if u is not None:
		return error_response(409, 'Username taken')
	u = User(
		username=new_username,
		email=new_email,
		password=new_password
	)
	db.session.add(u)
	# BetaCode specific
	beta_code = req_json['beta_code']
	if not check_and_assign_beta_code(beta_code, u):
		return error_response(400, 'Invalid beta code')
	db.session.commit()
	return {
		'message' : 'Successfully registered user',
		'user' : u.as_dict()
	}

@users.route('/<int:id>/auth/change-password', methods=['PATCH'])
@token_auth.login_required
@validation.validate_json_payload
def change_password(id):
	u = User.query.get_or_404(id)
	change_password_json = request.get_json()
	if not u.check_password(change_password_json['current_password']):
		return error_response(403, 'Current password incorrect')
	u.set_password(change_password_json['new_password'])
	db.session.commit()
	return {
		'message' : 'Successfully changed password',
		'user' : u.as_dict()
	}