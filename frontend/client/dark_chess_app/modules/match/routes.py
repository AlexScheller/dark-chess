import requests
from flask import render_template, redirect, url_for, jsonify, request, flash
from flask_login import current_user, login_required
from dark_chess_app.modules.match import match
from dark_chess_app.utilities.api_utilities import (
	api_request, authorized_api_request
)

@match.route('/create')
@login_required
def create_match():
	invited_id = request.args.get('invited_id', None)
	json = { 'invited_id': invited_id } if invited_id is not None else None
	create_match_res = authorized_api_request('/match/invite/create',
		requests.post,
		json=json
	)
	if create_match.status_code == 200:
		# invite_json = create_match_res.json()['match_invite']
		# redirect to match lobby
		flash('Created match.')
	elif create_match_res.status_code == 404:
		flash('No such opponent found, Unable to create match.')
	return redirect(url_for('main.index'))

@match.route('/invite/<int:id>/accept')
@login_required
def accept_match_invite(id):
	accept_invite_res = authorized_api_request(
		f'/match/invite/{id}/accept', requests.patch
	)
	if accept_invite_res.status_code == 200:
		match_json = accept_invite_res.json()['match']
		return redirect(url_for('match.match_page', id=match_json['id']))
	elif accept_invite_res.status_code == 403:
		flash('This match invite wasn\'t for you.', 'error')
	elif accept_invite_res.status_code == 410:
		flash('This match invite has already been accepted.', 'error')
	elif accept_invite_res.status_code == 404:
		flash('There\'s no such match invite.', 'error')
	else:
		flash('Unable to accept match invite.', 'error')
	return redirect(url_for('main.index'))

# Kept for when spectating becomes a thing

# @match.route('/<int:id>/join')
# @login_required
# def join_match(id):
# 	join_res = authorized_api_request(f'/match/{id}/join', requests.patch)
# 	# TODO handle errors
# 	return redirect(url_for('match.match_page', id=id))

@match.route('/open-matches')
@login_required
def open_matches():
	open_matches_res = authorized_api_request(f'/match/invite/query', requests.post,
		json={
			'is_open': True,
			'accepted': False
		}
	)
	open_matches = [
		m for m in open_matches_res.json()
		if m['inviter']['id'] != current_user.id
	]
	return render_template('match/open_match_invite_list.html',
		title='Match List',
		open_matches=open_matches
	)

# @match.route('/my-unnaccepted-invites')
# @login_required
# def users_unnaccepted_invites():
# 	invites_res = authorized_api_request('/match/invites/query', requests.post,
# 		json={
# 			'user_id': current_user.id,
# 			'accepted': False
# 		}
# 	)
# 	# TODO: Handle errors
# 	return render_template('match/active_match_invite_list.html',
# 		title='My Active Invites',
# 		invites=invites_res.json()
# 	)

@match.route('/my-match-invites')
@login_required
def users_match_invites():
	invites_res = authorized_api_request('/match/invite/query', requests.post,
		json={
			'involved_id': current_user.id,
			'accepted': False
		}
	)
	# TODO: Handle errors
	users_invites = []
	user_invited = []
	for invite in invites_res.json():
		if invite['inviter']['id'] == current_user.id:
			users_invites.append(invite)
		else:
			user_invited.append(invite)
	return render_template('match/users_match_invites.html',
		title='My Match Invites',
		users_invites=users_invites,
		user_invited=user_invited
	)

@match.route('/my-active-matches')
@login_required
def users_active_matches():
	matches_res = authorized_api_request(f'/match/query', requests.post,
		json={
			'user_id': current_user.id,
			'in_progress': True,
		}
	)
	# TODO: Handle errors
	return render_template('match/active_match_list.html',
		title='My Active Matches',
		matches=matches_res.json()
	)

@match.route('/<int:id>')
def match_page(id):
	match_res = authorized_api_request(f'/match/{id}')
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
	match_res = authorized_api_request(f'/match/{id}')
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