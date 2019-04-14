from flask import jsonify, g, request
from sqlalchemy import or_
from dark_chess_api import db
from dark_chess_api.modules.matches import matches
from dark_chess_api.modules.matches.models import Match
from dark_chess_api.modules.utilities import validation
from dark_chess_api.modules.auth.utils import token_auth
from dark_chess_api.modules.errors.handlers import error_response

### Query ###

# Convenience endpoints

@matches.route('/<int:id>', methods=['GET'])
@token_auth.login_required
def get_match(id):
	match = Match.query.get_or_404(id)
	return jsonify(match.as_dict())

@matches.route('/open-matches', methods=['GET'])
@token_auth.login_required
def get_open_matches():
	matches = Match.query.filter_by(open=True).all()
	return jsonify([m.id for m in matches])

# Master query endpoint

# Note that this endpoint allows potentially conflicting parameters.
# For example, if the requestor were to ask for all matches that
# were both open and in progress, they would get nothing in return.
# This endpoint leaves it up to the requestor to take that into
# account.
@matches.route('/query', methods=['POST'])
@token_auth.login_required
def query_matches():
	params = request.get_json()
	# maybe this should result in different behavior?
	if params is None:
		return jsonify({'matches' : []})
	matches = db.session.query(Match)
	if 'user_id' in params:
		uid = params['user_id']
		matches = matches.filter(
			or_(
				Match.player_black_id==uid,
				Match.player_white_id==uid
			)
		)
	if 'in_progress' in params:
		matches = matches.filter(
			Match.in_progress==params['in_progress']
		)
	if 'open' in params:
		matches = matches.filter(Match.open==True)
	return jsonify({
		'matches' : [m.as_dict() for m in matches.all()]
	})

### Actions ###
@matches.route('/create', methods=['POST'])
@token_auth.login_required
def create_match():
	player = g.current_user
	new_match = Match()
	db.session.add(new_match)
	new_match.join(player)
	db.session.commit()
	return jsonify({
		'message' : 'Successfully created match',
		'match' : new_match.as_dict()
	})

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
	return jsonify({
		'message' : 'Player successfully joined match.',
		'match' : match.as_dict()
	})

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
	return jsonify({
		'message' : 'Move successfully made',
		'match' : match.as_dict()
	})