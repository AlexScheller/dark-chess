from flask import jsonify, g, request
from sqlalchemy import or_

from dark_chess_api import db, endpointer
from dark_chess_api.modules.matches import matches
from dark_chess_api.modules.matches.models import Match
from dark_chess_api.modules.utilities import validation
from dark_chess_api.modules.users.auth import token_auth
from dark_chess_api.modules.errors.handlers import error_response
from dark_chess_api.modules.websockets import events as ws_events

### Query ###

# Convenience endpoints

# Previously you could just get any match you wanted, but obviously this allows
# for cheating. Until a robust spectating system is developed, you can only get
# your own matches, or previous matches. The below two routes are kept for
# posterity.

# @matches.route('/<int:id>', methods=['GET'])
# @token_auth.login_required
# def get_match(id):
# 	match = Match.query.get_or_404(id)
# 	return match.as_dict()

# @matches.route('/<int:id>/as-player', methods=['GET'])
# @token_auth.login_required
# def get_match_as_player(id):
# 	match = Match.query.get_or_404(id)
# 	if g.current_user.id == match.player_white_id:
# 		return match.as_dict('white')
# 	elif g.current_user.id == match.player_black_id:
# 		return match.as_dict('black')
# 	return error_response(403, 'You are not currently playing this match.')

@matches.route('/<int:id>', methods=['GET'])
@token_auth.login_required
def get_match(id):
	match = Match.query.get_or_404(id)
	if g.current_user.id == match.player_white_id:
		return match.as_dict(side='white')
	elif g.current_user.id == match.player_black_id:
		return match.as_dict(side='black')
	# if spectating: return match.as_dict(side='spectator')
	return match.as_dict(side=None)

@matches.route('/open-matches', methods=['GET'])
@token_auth.login_required
def get_open_matches():
	matches = Match.query.filter_by(open=True).all()
	return jsonify([m.as_dict() for m in matches])

# Master query endpoint

# Note that this endpoint allows potentially conflicting parameters.
# For example, if the requestor were to ask for all matches that
# were both open and in progress, they would get nothing in return.
# This endpoint leaves it up to the requestor to take that into
# account.
@endpointer.route('/query', methods=['POST'], bp=matches,
	accepts={
		'user_id': { 'type': 'integer' },
		'in_progress': { 'type': 'boolean' },
		'is_open': { 'type' : 'boolean', 'description': 'Whether or not the match can be joined' }
	},
	optional=['user_id', 'in_progress', 'is_open'],
	description='Query a list of matches'
)
@token_auth.login_required
def query_matches(user_id=None, in_progress=None, is_open=None):
	# maybe this should result in different behavior?
	if (user_id is None and in_progress is None and is_open is None):
		return jsonify([])
	matches = db.session.query(Match)
	if user_id is not None:
		matches = matches.filter(
			or_(
				Match.player_black_id==user_id,
				Match.player_white_id==user_id
			)
		)
	if in_progress is not None:
		matches = matches.filter(
			Match.in_progress==in_progress
		)
	if is_open is not None:
		matches = matches.filter(Match.open==is_open)
	return jsonify([m.as_dict() for m in matches.all()])

### Match Actions ###

@matches.route('/create', methods=['POST'])
@token_auth.login_required
def create_match():
	player = g.current_user
	new_match = Match()
	db.session.add(new_match)
	new_match.join(player)
	db.session.commit()
	return {
		'message' : 'Successfully created match',
		'match' : new_match.as_dict()
	}

@matches.route('/<int:id>/join', methods=['PATCH'])
@token_auth.login_required
def join_match(id):
	match = Match.query.get_or_404(id)
	if not match.open:
		return error_response(403,
			'Match is full'
		)
	player = g.current_user
	if match.playing(player):
		return error_response(409,
			'Player is already in match'
		)
	match.join(player)
	db.session.commit()
	ws_events.broadcast_match_begun(match.connection_token)
	return {
		'message' : 'Player successfully joined match.',
		'match' : match.as_dict()
	}

### In Game Actions ###

@matches.route('/<int:id>/make-move', methods=['POST'])
@token_auth.login_required
@validation.validate_json_payload
def make_move(id):
	match = Match.query.get_or_404(id)
	player = g.current_user
	if not match.playing(player):
		return error_response(403,
			'Player not playing this match'
		)
	if not match.players_turn(player):
		return error_response(409,
			'Not your turn'
		)
	req_json = request.get_json()
	if not match.attempt_move(player, req_json['uci_string']):
		return error_response(422,
			'Move not possible'
		)
	db.session.commit()
	ws_events.broadcast_move_made(
		player=player,
		move=req_json['uci_string'],
		current_fen=match.current_fen,
		connection_token=match.connection_token
	)
	if match.is_finished:
		ws_events.broadcast_match_finish(
			winning_player=player,
			connection_token=match.connection_token
		)
	return {
		'message' : 'Move successfully made',
		'match' : match.as_dict()
	}