from flask import jsonify, g, request
from dark_chess_api import db
from dark_chess_api.modules.matches import matches
from dark_chess_api.modules.matches.models import Match
from dark_chess_api.modules.utilities import validation
from dark_chess_api.modules.auth.utils import token_auth
from dark_chess_api.modules.errors.handlers import error_response

### Query ###

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
	if match.playing(player.id):
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
	if not match.playing(player.id):
		return error_response(403,
			'Player not playing this match'
		)
	if not match.players_turn(player.id):
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