from dark_chess_api import create_app, db, cli
from dark_chess_api.modules.users.models import User

app = create_app()
cli.init(app)

@app.shell_context_processor
def make_shell_context():
	return {
		'db': db,
		'User': User
	}