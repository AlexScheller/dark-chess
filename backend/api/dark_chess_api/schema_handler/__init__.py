from functools import wraps
from jsonschema import (
	validate as validate_json,
	ValidationError
)
from copy import deepcopy

from flask import request, jsonify, abort


# Custom middleware used to both validate and pass on payload arguments directly
# to routes.

class Schema:

	# Methods should perhaps be automagical from the `route` decorator.

	# How should required be handled? Basically should providing None mean everything
	# is required or nothing is required? Probably the most idiomatic to make it mean
	# nothing is required, but this will put more burdon on the syntax of the decorators...
	def __init__(self, name, value_schema=None, optional=[], methods=['GET']):
		self.name = name
		self.methods = methods
		self.value_schema = value_schema
		self.required = [key for key in value_schema if key not in optional]
		self.reference_schema = self._generate_reference_schema(value_schema, self.required)
		self.validation_schema = {
			'type': 'object',
			'properties': deepcopy(self.value_schema),
			'required': self.required
		}

	def _generate_reference_schema(self, value_schema, required):
		ret = deepcopy(value_schema)
		for key, value in ret.items():
			value['required'] = (key in required)
		return ret

	def __str__(self):
		return f'<{self.name} {self.method}>'

class NoSchemaError(Exception):
	pass

class SchemaHandler:

	def __init__(self, app=None, error_handler=None):

		self.app = None
		self.schemas = {}
		self._error_handler = None

		if app is not None:
			self.init_app(app, error_handler)

	def init_app(self, app, error_handler=None):
		self.app = app
		self._error_handler = error_handler

	def handle_error_response(self, code, message):
		if self._error_handler is not None:
			return self._error_handler(code, message)
		return abort(code)

	def accepts(self, schema, required=[]):
		def decorated(func):
			# This check might be unnecessary since this is only called "once"
			# on application creation/startup.
			if func.__name__ not in self.schemas:
				self.schemas[func.__name__] = Schema(func.__name__, schema, required)
			working_schema = self.schemas[func.__name__]
			@wraps(func)
			def wrapped(*args, **kwargs):
				payload = request.get_json()
				if payload is None:
					return self.handle_error_response(400, 'No JSON payload.')
				# Basically a help message
				if 'schema' in payload:
					return jsonify(working_schema.reference_schema)
				try:
					# We don't bother to check for SchemaError, since that
					# *should* cause the program to crash since it's a breaking
					# bug that needs to be dealt with.
					validate_json(payload, working_schema.validation_schema)
				except ValidationError as e:
					return self.handle_error_response(400, e.message)
				for key in working_schema.value_schema:
					if key in payload:
						kwargs[key] = payload[key]
					# Things could be handled the way below, but instead we
					# handle them the above way in order to defer to the route
					# itself for how to handle default/null values
					# value = payload[key] if key in payload else None
					# kwargs[key] = value
				return func(*args, **kwargs)
			return wrapped
		return decorated