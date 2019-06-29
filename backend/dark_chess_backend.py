from dark_chess_api import create_app, db, cli, custom_jinja_filters, socketio
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

# Flask-SocketIO no longer supports the werkzeug dev server or the
# `flask run` command, so the application must be started via the
# below with `python dark_chess_backend.py` with `eventlet` or
# `gevent` installed. In production of course it will work with
# gunicorn in the regular fashion.
if __name__ == '__main__':
	socketio.run(app, debug=True)