import requests
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from dark_chess_app.modules.match import match
from dark_chess_app.utilities.api_utilities import (
	api_request, api_token_request
)
from dark_chess_app.modules.errors.handlers import api_error_response

@match.route('/create')
@login_required
def create_match():
	create_match_res = api_token_request('/match/create', requests.post)
	match_json = create_match_res.json()['match']
	# TODO handle errors
	return redirect(
		url_for('match.match_page', id=match_json['id'])
	)

@match.route('/<int:id>/join')
@login_required
def join_match(id):
	join_res = api_token_request(f'/match/{id}/join', requests.patch)
	# TODO handle errors
	return redirect(url_for('match.match_page', id=id))

@match.route('/open-matches')
@login_required
def open_matches():
	open_matches_res = api_token_request(f'/match/open-matches')
	return render_template('match/match_list.html',
		title='Match List',
		matches=open_matches_res.json()
	)

@match.route('/my-active-matches')
@login_required
def users_active_matches():
	matches_res = api_token_request(f'/match/query', requests.post,
		json={
			'user_id': current_user.id,
			'in_progres': True,
		}
	)
	return render_template('match/match_list.html',
		title='My Active Matches',
		matches=matches_res.json()
	)

@match.route('/<int:id>')
def match_page(id):
	match_res = api_token_request(f'/match/{id}')
	if match_res.status_code == 404:
		flash('No such match')
		return redirect(url_for('match.match_list'))
	match_json = match_res.json()
	return render_template('match/match.html',
		title=match_json['id'],
		match=match_json
	)

######################
#  API Proxy Routes  #
######################

@match.route('/api/<int:id>')
@login_required
def api_get_match(id):
	match_res = api_token_request(f'/match/{id}')
	if match_res.status_code != 200:
		return api_error_response(match_res.status_code)
	match_json = match_res.json()
	return jsonify(match_json)

@match.route('/api/<int:id>/make-move', methods=['POST'])
@login_required
def api_make_move(id):
	move_json = request.get_json()
	move_res = api_token_request(f'/match/{id}/make-move', requests.post,
		json={
			'uci_string': move_json['uci_string']
		}
	)
	if move_res.status_code != 200:
		return api_error_response(move_res.status_code)
	move_json = move_res.json()
	return jsonify(move_json)