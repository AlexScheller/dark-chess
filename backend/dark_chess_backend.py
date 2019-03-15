from dark_chess_api import create_app, db, cli, custom_jinja_filters
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.matches.models import Match

app = create_app()
cli.init(app)
custom_jinja_filters.init(app)

@app.shell_context_processor
def make_shell_context():
	return {
		'db': db,
		'User': User,
		'Match': Match
	}