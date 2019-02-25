import os
import jsonschema
from functools import wraps
from flask import request, json, current_app, jsonify
from jsonschema.exceptions import ValidationError
from dark_chess_api.modules.errors.handlers import error_response

def load_schemas(schema_folder):
	ret = {}
	for file in os.listdir(os.fsencode(schema_folder)):
		file_name = os.fsdecode(file)
		file_path = os.path.join(schema_folder, file_name)
		with open(file_path, 'r') as schema_file:
			ret[file_name.split('_')[0]] = json.load(schema_file)
	return ret

# Used to wrap all routes that expect a json payload. This
# function validates the payload against a hand created
# schema located in `/static/schemas/<module>_schemas.json`.
# It is important to note the the schema is selected using
# the name of the wrapped function, so there must be a
# matching schema in the `<module>_schemas.json` file for
# this to work. Additionally, the module name is taken from
# the module that the route is in, so that also needs to
# match up, e.g. `dark_chess_api.modules.users.endpoints`.
# Were this not a specialized wrapper meant for this project
# alone, a more explicit method of passing module and schmema
# names (i.e. in the form of parameters) would certainly be
# preferred for readability and maintainability.
def validate_json_payload(func):
	@wraps(func)
	def decorated(*args, **kwargs):
		payload = request.get_json()
		if payload is None:
			return error_response(400, 'No JSON payload.')
		endpoint_schema = current_app.endpoint_schemas[func.__module__.split('.')[-2]][func.__name__]
		if 'schema' in payload:
			return jsonify(endpoint_schema)
		try:
			# If there is a key error in `endpoint_schemas`,
			# then the program *should* be allowed to crash,
			# since if a route cannot be validated, it is
			# likely to cause a crash itself sooner rather
			# than later.
			jsonschema.validate(payload, endpoint_schema)
		except ValidationError as e:
			return error_response(400, e.message)
		return func(*args, **kwargs)
	return decorated