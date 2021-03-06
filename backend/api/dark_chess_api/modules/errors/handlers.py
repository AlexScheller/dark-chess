# The following error handling code heavliy references "microblog",
# (see README.md)

from flask import jsonify, request
from dark_chess_api import db
from dark_chess_api.modules.errors import errors
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
	payload = {
		'error' : HTTP_STATUS_CODES.get(status_code, 'Unknown error')
	}
	if message:
		payload['message'] = message
	response = jsonify(payload)
	response.status_code = status_code
	return response

@errors.app_errorhandler(500)
def internal_server_error(error):
	db.session.rollback()
	return error_response(500)

@errors.app_errorhandler(405)
def not_found_error(error):
	return error_response(405)

@errors.app_errorhandler(404)
def not_found_error(error):
	return error_response(404)

@errors.app_errorhandler(401)
def unauthorized_error(error):
	return error_response(401)

@errors.app_errorhandler(400)
def unauthorized_error(error):
	return error_response(400)