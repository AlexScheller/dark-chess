import requests

from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required

from dark_chess_app.modules.user import user
from dark_chess_app.modules.user.forms import UserSearchForm
from dark_chess_app.utilities.api_utilities import api_token_request

@user.route('/profile')
@login_required
def current_user_profile():
	user_res = api_token_request(f'/user/{current_user.id}')
	if user_res.status_code != 200:
		abort(user_res.status_code)
	user_data = user_res.json()
	return render_template('user/current_user_profile.html',
		title=user_data['username'],
		user=user_data
	)

@user.route('/<int:id>/profile')
@login_required
def user_profile(id):
	user_res = api_token_request(f'/user/{id}')
	if user_res.status_code != 200:
		abort(user_res.status_code)
	user_data = user_res.json()
	is_friend = current_user.id in [f.id for f in user_data['friends']]
	return render_template('user/user_profile.html',
		title=user_data['username'],
		user=user_data,
		is_friend=is_friend,
		is_user=(user_data['id']==current_user.id)
	)

@user.route('/search', methods=['GET', 'POST'])
@login_required
def user_search():
	form = UserSearchForm()
	results = None
	if form.validate_on_submit():
		search_request = api_token_request('/user/search',
			method=requests.post,
			json={ 'username': form.username.data }
		)
		if search_request.status_code != 200:
			flash('Unable to load search results', 'error')
			return redirect(url_for('main.index'))
		results = search_request.json()
	return render_template('user/user_search.html',
		title='Search Results',
		form=form,
		results=results
	)