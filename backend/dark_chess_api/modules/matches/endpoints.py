from flask import jsonify, g
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
@validation.validate_json_payload
def join_match(id):
	match = Match.query.get_or_404(id)
	if not match.open:
		return error_response(403,
			'Match is full'
		)
	req_json = request.get_json()
	player = Player.query.get(req_json['player_id'])
	if player is None:
		return error_response(400,
			f'No player found for id: {req_json["player_id"]}'
		)
	match.join(player)
	db.session.commit()
	return jsonify({
		'message' : 'Player successfully joined match.',
		'match' : match.as_dict()
	})