from flask import json

# Currently the only filter present in this template is unused,
# but the file will remain, since it may be used in the future.
# If the documentation pages reach a conclusive point without
# the need for this file, it should be removed.
def init(app):

	@app.template_filter('to_pretty_json')
	def to_pretty_json(value):
		print(type(value))
		return json.dumps(value, indent=4, sort_keys=True)