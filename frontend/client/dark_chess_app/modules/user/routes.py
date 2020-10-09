import requests
from flask import render_template, request
from flask_login import current_user, login_required
from dark_chess_app.modules.user import user
from dark_chess_app.utilities.api_utilities import api_token_request

@user.route('/profile')
@login_required
def current_user_profile():
	user_res = api_token_request(f'/user/{current_user.id}')
	if user_res.status_code != 200:
		abort(user_res.status_code)
	user_data = user_res.json()
	return render_template('user/current_user_profile.html',
		user=user_data
	)

@user.route('/<int:id>/profile')
@login_required
def user_profile(id):
	user_res = api_token_request(f'/user/{id}')
	if user_res.status_code != 200:
		abort(user_res.status_code)
	user_data = user_res.json()
	return render_template('user/user_profile.html',
		user=user_data
	)