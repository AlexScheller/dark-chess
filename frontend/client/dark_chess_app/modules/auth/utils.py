from flask_login import current_user
from functools import wraps
from dark_chess_app.modules.errors.handlers import api_error_response 

def proxy_login_required(endpoint):
	@wraps(endpoint)
	def decorated_endpoint(*args, **kwargs):
		if not current_user.is_authenticated:
			return api_error_response(401)
		return endpoint(*args, **kwargs)
	return decorated_endpoint