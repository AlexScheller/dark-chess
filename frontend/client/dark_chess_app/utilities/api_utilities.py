import requests
from flask import current_app, flash, abort, redirect, url_for
from flask_login import current_user, logout_user

def api_route(endpoint, **kwargs):
	return f'{current_app.config["API_ROOT"]}{endpoint}'

# Note that 'method' here takes a function from the
# 'requests' library, e.g. `api_requests(requests.get, '/foo')`
def api_request(endpoint, method=requests.get, **kwargs):
	return method(api_route(endpoint), **kwargs)

def authorized_api_request(endpoint, method=requests.get, **kwargs):
	if 'headers' in kwargs:
		kwargs['headers']['Authorization'] = f'Bearer {current_user.token}'
	else:
		kwargs['headers'] = {
			'Authorization': f'Bearer {current_user.token}'
		}
	req = api_request(endpoint, method, **kwargs)
	if req.status_code == 401: # token auth failed
		flash('Your session has expired, please log in again.')
		logout_user()
		abort(401) # login redirect is handled by app level error handler.
	return req