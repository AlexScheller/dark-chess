from functools import wraps
from jsonschema import (
	validate as validate_json,
	ValidationError
)
from copy import deepcopy

from flask import request, jsonify, abort


# Custom middleware used to both validate and pass on payload arguments directly
# to routes.

class Endpoint:

	# Methods should perhaps be automagical from the `route` decorator.

	# How should required be handled? Basically should providing None mean everything
	# is required or nothing is required? Probably the most idiomatic to make it mean
	# nothing is required, but this will put more burdon on the syntax of the decorators...
	def __init__(self, name,
		responses=None,
		acceptance_schema=None,
		optional=[],
		methods=['GET']
	):
		self.name = name
		self.methods = methods
		self.optional = optional
		if responses is not None:
			self.init_responds(responses)
		if acceptance_schema is not None:
			self.init_accepts(acceptance_schema)

	def init_accepts(self, acceptance_schema):
		self.schema_base = acceptance_schema
		self.required = [
			key for key in self.schema_base if key not in self.optional
		]
		self.reference_schema = deepcopy(self.schema_base)
		for key, value in self.reference_schema.items():
			value['required'] = (key in self.required)
		self.validation_schema = {
			'type': 'object',
			'properties': deepcopy(self.schema_base),
			'required': self.required
		}

	def init_responds(self, responses):
		self.responses = responses

	@property
	def payload_fully_optional(self):
		return len(self.required) == 0

	def __str__(self):
		return f'<{self.name} {self.method}>'

class NoSchemaError(Exception):
	pass

class EndpointHandler:

	def __init__(self, app=None, error_handler=None):

		self.app = None
		self.endpoints = {}
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

	def accepts(self, schema, optional=[]):
		def decorated(func):
			if func.__name__ not in self.endpoints:
				self.endpoints[func.__name__] = Endpoint(
					func.__name__, acceptance_schema=schema, optional=optional
				)
			else:
				self.endpoints[func.__name__].init_accepts(schema)
			endpoint = self.endpoints[func.__name__]
			@wraps(func)
			def wrapped(*args, **kwargs):
				payload = request.get_json()
				if payload is None:
					if endpoint.payload_fully_optional:
						return func(*args, **kwargs)
					return self.handle_error_response(400, 'No JSON payload.')
				# Basically a help message
				if 'help' in payload or 'schema' in payload:
					return jsonify(endpoint.reference_schema)
				try:
					# We don't bother to check for SchemaError, since that
					# *should* cause the program to crash since it's a breaking
					# bug that needs to be dealt with.
					validate_json(payload, endpoint.validation_schema)
				except ValidationError as e:
					return self.handle_error_response(400, e.message)
				for key in endpoint.schema_base:
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

	# This route is mainly only for documentation purposes
	def responds(self, codes):
		def decorated(func):
			if func.__name__ not in self.endpoints:
				self.endpoints[func.__name__] = Endpoint(
					func.__name__, responses=codes
				)
			else:
				self.endpoints[func.__name__].init_responds(codes)
			endpoint = self.endpoints[func.__name__]
			@wraps(func)
			def wrapped(*args, **kwargs):
				# Todo return help message
				return func(*args, **kwargs)
			return wrapped
		return decorated