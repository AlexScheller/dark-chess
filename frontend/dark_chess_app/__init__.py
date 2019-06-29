from flask import Flask
from flask_login import LoginManager
from flask_talisman import Talisman
from config import Config

login = LoginManager()
talisman = Talisman()

def create_app(config=Config):

	app = Flask(__name__)
	app.config.from_object(config)

	login.init_app(app)
	login.login_view = 'auth.login'

	SELF = '\'self\''

	csp = {
		'default-src': [
			SELF,
			'pro.fontawesome.com'
		],
		'script-src': [
			SELF,
			'cdnjs.cloudflare.com'
		],
		'connect-src': [
			SELF,
			'http://localhost:5000',
			'ws://localhost:5000'
		]
	}
	talisman.init_app(app, content_security_policy=csp)

	from dark_chess_app.modules.errors import errors
	app.register_blueprint(errors)

	from dark_chess_app.modules.main import main
	app.register_blueprint(main)

	from dark_chess_app.modules.auth import auth
	app.register_blueprint(auth, url_prefix='/auth')

	from dark_chess_app.modules.match import match
	app.register_blueprint(match, url_prefix='/match')

	app.jinja_env.lstrip_blocks = True
	app.jinja_env.trim_blocks = True

	return app
