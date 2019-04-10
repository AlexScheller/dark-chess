import requests
from flask import current_app
from flask_login import current_user


def api_route(endpoint, **kwargs):
	return f'{current_app.config["API_ROOT"]}{endpoint}'

# Note that 'method' here takes a function from the
# 'requests' library, e.g. `api_requests(requests.get, '/foo')`
def api_request(endpoint, method=requests.get, **kwargs):
	return method(api_route(endpoint), **kwargs)

def api_token_request(endpoint, method=requests.get, **kwargs):
	if 'headers' in kwargs:
		kwargs['headers']['Authorization'] = f'Bearer {current_user.token}'
	else:
		kwargs['headers'] = {
			'Authorization': f'Bearer {current_user.token}'
		}
	return api_request(endpoint, method, **kwargs)