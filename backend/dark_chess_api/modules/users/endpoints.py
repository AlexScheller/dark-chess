from flask import g, jsonify, request
from dark_chess_api import db
from dark_chess_api.modules.users import users
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.auth.utils import basic_auth

@users.route('/auth/token', methods=['GET'])
@basic_auth.login_required
def aquire_token():
	token = g.current_user.get_token()
	db.session.commit()
	return jsonify({
		'token' : token,
		'user' : g.current_user.as_dict()
	})


@users.route('/auth/register', methods=['POST'])
def register_user():
	registration_json = request.get_json()
	u = User(
		username=registration_json['username'],
		password=registration_json['password']
	)
	db.session.add(u)
	db.session.commit()
	return jsonify({
		'message' : 'Successfully registered user.',
		'user' : u.as_dict()
	})