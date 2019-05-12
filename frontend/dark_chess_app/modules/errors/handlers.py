from flask import redirect, url_for
from dark_chess_app.modules.errors import errors

@errors.app_errorhandler(401)
def unauthorized_error(error):
	return redirect(url_for('auth.login'))