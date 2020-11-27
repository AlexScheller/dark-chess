from functools import wraps
from jsonschema import (
	validate as validate_json,
	ValidationError
)
from werkzeug.http import HTTP_STATUS_CODES
from copy import deepcopy

from flask import request, jsonify, render_template, abort, Blueprint

# Custom middleware used to both validate and pass on payload arguments directly
# to routes. This is it's own module a level above the app specific modules as
# I'd like to make it as application agnostic as possible for future reuse.

# Some ideas are taken from Miguel Grinberg's APIFairy project, which can be
# found at https://github.com/miguelgrinberg/APIFairy

class Endpointer:

	def __init__(self,
		app=None,
		documentation_root='docs',
		error_handler=None,
		help_keyword='help'
	):
		self.app = None
		self.endpoints = {}
		self.resources = {}
		self._error_handler = None
		self.documentation_root = documentation_root
		self.help_keyword = help_keyword

		if app is not None:
			self.init_app(app, error_handler)

	def init_app(self, app, error_handler=None):
		self.app = app
		self._error_handler = error_handler

		# for name in app.blueprints:
		# 	self._blueprints[name] = Resource(name, self._error_handler)
		# 	setattr(self, name, self._blueprints[name])

		bp = Blueprint('endpoint_handler', __name__, template_folder='templates')

		# Browser based documentation pages. Request-based documentation is
		# handled in the decorator.

		@bp.route('/')
		@bp.route('/index')
		def doc_hub():
			resources = self.resources.keys()
			return render_template('documentation_hub.html',
				resources=resources
			)

		@bp.route('/<string:resource>')
		def doc_page(resource):
			if resource in self.resources:
				return render_template('resource_doc_page.html',
					current_resource=self.resources[resource].as_dict(),
					all_resources=self.resources.keys()
				)
			abort(404)

		app.register_blueprint(bp, url_prefix=f'/{self.documentation_root}')

	def handle_error_response(self, code, message):
		if self._error_handler is not None:
			return self._error_handler(code, message)
		return abort(code)

	def route(self, rule, *args, bp=None, accepts=None, optional=[], responds=None, **kwargs):
		# Resource bookkeeping
		resource_name = bp.name if bp is not None else '__root__'
		if resource_name not in self.resources:
			self.resources[resource_name] = Resource(
				resource_name, self.handle_error_response
			)
		resource = self.resources[resource_name]
		def decorated(endpoint):
			# Endpoint bookkeeping
			method = 'GET'
			if 'methods' in kwargs:
				if len(kwargs['methods']) > 1:
					raise ValueError(f'Flask-Endpointer requires routes to consist of a single method, {endpoint.__name__} was passed {kwargs["methods"]}.')
				method = kwargs['methods'][0]
			new_endpoint = Endpoint(endpoint, method=method)
			if accepts is not None:
				new_endpoint.init_accepts(accepts, optional)
			if responds is not None:
				new_endpoint.init_responds(responds)
			resource.register_endpoint(new_endpoint)
			# "Wrap" it all up
			# Does this work?
			wrapper = bp if bp is not None else self.app
			@wrapper.route(rule, *args, **kwargs)
			@wraps(endpoint)
			def inner(*args, **kwargs):
				if accepts is not None or responds is not None:
					if request.args.get(self.help_keyword, None) is not None:
						return new_endpoint.help_dict
				if accepts is not None:
					payload = request.get_json()
					if payload is None:
						if new_endpoint.payload_fully_optional:
							return endpoint(*args, **kwargs)
						return self.handle_error_response(400, 'No JSON payload.')
					try:
						# We don't bother to check for SchemaError, since
						# that *should* cause the program to crash. A Schema
						# error is caused by incorrectly formatting the
						# schema dict, and so should be considered an
						# application breaking bug, as the whole point of
						# this middleware is to marry documentation and
						# code. 
						validate_json(payload, new_endpoint.validation_schema)
					except ValidationError as e:
						return self.handle_error_response(400, e.message)
					for key in new_endpoint.schema_base:
						if key in payload:
							kwargs[key] = payload[key]
				return endpoint(*args, **kwargs)
			return inner
		return decorated

class Resource:

	def __init__(self, name, error_handler=None):
		self.name = name
		self.endpoints = {}
		self._error_handler = error_handler

	def register_endpoint(self, endpoint):
		self.endpoints[endpoint.name] = endpoint

	def handle_error_response(self, code, message):
		if self._error_handler is not None:
			return self._error_handler(code, message)
		return abort(code)

	def as_dict(self):
		return {
			'endpoints': [
				endpoint.as_dict()
			] for endpoint in self.endpoints.values()
		}

class Endpoint:

	# Note that currently only one method is allowed to be specified. This fits
	# with my style of creating routes, where I would create two separate routes
	# for two separate methods, but not everyone does things that way.
	def __init__(self, name,
		responses=None,
		acceptance_schema=None,
		optional=[],
		method='GET'
	):
		self.name = name
		self.method = method
		self.optional = optional
		# Hopefully it's not to much of an assumption on my part that every
		# route can respond with 200?
		self.responses = { 200: { 'message': '[Successful response]' } }
		if responses is not None:
			self.init_responds(responses)
		if acceptance_schema is not None:
			self.init_accepts(acceptance_schema)

	def init_accepts(self, acceptance_schema, optional):
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
		# If there's an acceptance schema than it's basically (but I guess not
		# fully) guaranteed to potentially return a 400. If a user provides a
		# custom response for 400 in the `responds` dict, that will overwrite
		# this. If it becomes too annoying that 400 is automatically injected
		# here it can easily be removed.
		self.responses[400] = {
			'error': 'Bad Request',
			'message': '[Validation error content]'
		}

	def init_responds(self, responses):
		self.responses.update(responses)
		for code in self.responses:
			if self.responses[code] is None:
				self.responses[code] = {
					'error': HTTP_STATUS_CODES.get(code, 'Unknown error'),
					'message': '[Error message content]'
				}

	@property
	def payload_fully_optional(self):
		return len(self.required) == 0

	def __str__(self):
		return f'<{self.name} {self.method}>'

	@property
	def help_dict(self):
		return {
			'payload': self.reference_schema,
			'responses': self.responses
		}

	def as_dict(self):
		return {
			'name': self.name,
			'method': self.method
		}