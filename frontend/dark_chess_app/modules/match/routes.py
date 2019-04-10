import requests
from flask import render_template, redirect, url_for
from flask_login import current_user
from dark_chess_app.modules.match import match
from dark_chess_app.utilities.api_utilities import (
	api_request, api_token_request
)

@match.route('/create')
def create_match():
	create_match_res = api_token_request(f'/match/create',
		method=requests.post
	)
	match_json = create_match_res.json()['match']
	# TODO handle errors
	return redirect(
		url_for('match.match_page', id=match_json['id'])
	)

@match.route('/<int:id>/join')
def join_match(id):
	join_res = api_token_request(f'/match/{id}/join',
		method=requests.patch
	)
	# TODO handle errors
	return redirect(url_for('match.match_page', id=id))

@match.route('/open-matches')
def open_matches():
	open_matches_res = api_token_request(f'/match/open-matches')
	return render_template('match/open_matches.html',
		title='Match List',
		matches=open_matches_res.json()
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