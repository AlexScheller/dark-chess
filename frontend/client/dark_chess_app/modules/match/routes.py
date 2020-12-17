import requests
from flask import render_template, redirect, url_for, jsonify, request, flash
from flask_login import current_user, login_required
from dark_chess_app.modules.match import match
from dark_chess_app.utilities.api_utilities import (
	api_request, api_token_request
)

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
			'in_progress': True,
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
		return redirect(url_for('match.open_matches'))
	match_json = match_res.json()
	player_color = None
	if match_json['player_black'] and match_json['player_black']['id'] == current_user.id:
		player_color = 'black'
	elif match_json['player_white'] and match_json['player_white']['id'] == current_user.id:
		player_color = 'white'
	return render_template('match/match.html',
		title=match_json['id'],
		match=match_json,
		player_color=player_color
	)

@match.route('/<int:id>/history')
def match_history(id):
	match_res = api_token_request(f'/match/{id}')
	if match_res.status_code == 404:
		flash('No such match')
		return redirect(url_for('match.open_matches'))
	match_json = match_res.json()
	history = []
	if 'white_vision_history' in match_json:
		history = match_json['white_vision_history']
	elif 'black_vision_history' in match_json:
		history = match_json['black_vision_history']
	elif 'transparent_history' in match_json:
		history = match_json['transparent_history']
	expanded_history = []
	for fen in history:
		expanded_history.append([row for row in fen.split('/')])
	return render_template('match/history.html',
		title=f'{match_json["id"]} history',
		history=expanded_history,
		match=match_json
	)