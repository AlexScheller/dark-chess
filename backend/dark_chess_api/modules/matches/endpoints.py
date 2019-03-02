from flask import jsonify
from dark_chess_api.modules.matches import matches
from dark_chess_api.modules.matches.models import Match
from dark_chess_api.modules.utilities import validation
from dark_chess_api.modules.auth.utils import token_auth
from dark_chess_api.modules.errors.handlers import error_response

### Query ###

@matches.route('/<int:id>', methods=['GET'])
def get_match(id):
	match = Match.query.get_or_404(id)
	return jsonify(match.as_dict())

@matches.route('/open-matches', methods=['GET'])
def get_open_matches():
	matches = Match.query.filter_by(open=True).all()
	return jsonify([m.id, for m in matches])

### Actions ###
@matches.route('/create', methods=['POST'])
@validation.validate_json_payload
def create_match(id):
	req_json = request.get_json()
	player = Player.query.get(req_json['player_id'])
	if player is None:
		return error_response(400,
			f'No player found for id: {req_json['player_id']}'
		)
	new_match = Match(player=player)
	db.session.add(new_match)
	db.session.commit()
	return jsonify({
		'message' : 'Successfully created match',
		'match' : new_match.as_dict()
	})

@matches.route('/<int:id>/join', methods=['POST'])
@validation.validate_json_payload
def join_match(id):
	match = Match.query.get_or_404(id)
	req_json = request.get_json()
	player = Player.query.get(req_json['player_id'])
	if player is None:
		return error_response(400,
			f'No player found for id: {req_json['player_id']}'
		)
	if match.open:
		join(player)
		db.session.commit()
	return jsonify({
		'message' : 'Player successfully joined match.',
		'match' : match.as_dict()
	})