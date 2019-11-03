from flask import redirect, url_for, jsonify
from dark_chess_app.modules.errors import errors
from werkzeug.http import HTTP_STATUS_CODES

def json_response_requested(request):
	return (request.accept_mimetypes['application/json'] >=
			request.accept_mimetypes['text/html'])

def api_error_response(status_code, message=None):
	payload = {
		'error' : HTTP_STATUS_CODES.get(status_code, 'Unkown error')
	}
	if message:
		payload['message'] = message
	response = jsonify(payload)
	response.status_code = status_code
	return response

# TODO see if this is even called from proxy routes.
@errors.app_errorhandler(401)
def unauthorized_error(error):
	if json_response_requested(request):
		return api_error_response(401)
	return redirect(url_for('auth.login'))