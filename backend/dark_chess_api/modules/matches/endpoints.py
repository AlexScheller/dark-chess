from flask import jsonify
from dark_chess_api.modules.matches import matches
from dark_chess_api.modules.matches.models import Match
from dark_chess_api.modules.utilities import validation
from dark_chess_api.modules.auth.utils import token_auth
from dark_chess_api.modules.errors.handlers import error_response

@matches.route('/<int:id>', methods=['GET'])
def get_match(id):
	match = Match.query.get_or_404(id)
	return jsonify({
		'match' : match.as_dict()
	})