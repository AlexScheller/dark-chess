import requests
from flask import current_app

def api_route(endpoint, **kwargs):
	return f'{current_app.config["API_ROOT"]}{endpoint}'

# Note that 'method' here takes a function from the
# 'requests' library, e.g. `api_requests(requests.get, '/foo')`
def api_request(method, endpoint, **kwargs):
	return method(api_route(endpoint), **kwargs)

def api_token_request(method, endpoint, **kwargs):
	if 'headers' in kwargs:
		kwargs['headers']['Authorization'] = f'Bearer {current_user.token}'
	return api_request(method, endpoint, **kwargs)