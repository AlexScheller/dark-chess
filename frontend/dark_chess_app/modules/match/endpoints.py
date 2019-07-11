import requests
from flask import request
from flask_login import login_required
from dark_chess_app.modules.match import match
from dark_chess_app.utilities.api_utilities import api_token_request
from dark_chess_app.modules.errors.handlers import api_error_response

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
	return match_json

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
	return move_json