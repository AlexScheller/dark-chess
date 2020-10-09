from flask import redirect, url_for, jsonify, request, render_template
from functools import wraps
from dark_chess_app.modules.errors import errors
from werkzeug.http import HTTP_STATUS_CODES

def json_response_requested(request):
	return (request.accept_mimetypes['application/json'] >=
			request.accept_mimetypes['text/html'])

def json_handler(error_code):
	def wrapper(handler):
		@wraps(handler)
		def decorated_handler(*args, **kwargs):
			if json_response_requested(request):
				return api_error_response(error_code)
			return handler(*args, **kwargs)
		return decorated_handler
	return wrapper

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
@json_handler(401)
def unauthorized_error(error):
	return redirect(url_for('auth.login'))

@errors.app_errorhandler(404)
@json_handler(404)
def not_found_error(error):
	return render_template('errors/404.html',
		code=404,
		message=HTTP_STATUS_CODES.get(404)
	), 404