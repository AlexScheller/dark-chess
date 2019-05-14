from flask import redirect, url_for
from dark_chess_app.modules.errors import errors
from werkzeug.http import HTTP_STATUS_CODES

def api_error_response(status_code, message=None):
	payload = {
		'error' : HTTP_STATUS_CODES.get(status_code, 'Unkown error')
	}
	if message:
		payload['message'] = message
	response = jsonify(payload)
	response.status_code = status_code
	return response

@errors.app_errorhandler(401)
def unauthorized_error(error):
	return redirect(url_for('auth.login'))