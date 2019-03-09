from flask import current_app, render_template
from dark_chess_api.modules.docs import docs

@docs.route('/')
@docs.route('/index')
def index():
	resources = current_app.endpoint_schemas.keys()
	return render_template('docs/index.html',
		resources=resources
	)

@docs.route('/<string:resource>/endpoints')
def doc_page(resource):
	if resource not in current_app.endpoint_schemas:
		abort(404)
	resources = current_app.endpoint_schemas.keys()
	endpoint_schemas = current_app.endpoint_schemas[resource]
	return render_template('docs/endpoint_doc_page.html',
		resources=resources,
		current_resource=resource,
		endpoint_schemas=endpoint_schemas
	)