import logging
from logging.handlers import SMTPHandler

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
			app.config['API_ROOT'],
			f'ws://{app.config["API_DOMAIN_AND_PORT"]}'
		]
	}
	# We will enforce https upstream with nginx
	talisman.init_app(app,
		force_https=False,
		content_security_policy=csp
	)

	from dark_chess_app.modules.errors import errors
	app.register_blueprint(errors)

	from dark_chess_app.modules.main import main
	app.register_blueprint(main)

	from dark_chess_app.modules.auth import auth
	app.register_blueprint(auth, url_prefix='/auth')

	from dark_chess_app.modules.user import user
	app.register_blueprint(user, url_prefix='/user')

	from dark_chess_app.modules.match import match
	app.register_blueprint(match, url_prefix='/match')

	app.jinja_env.lstrip_blocks = True
	app.jinja_env.trim_blocks = True

	if not app.debug and app.config['MAIL_SERVER'] and app.config['ERROR_REPORT_EMAIL']:
		auth = None
		if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
			auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
		secure = () if app.config['MAIL_USE_TLS'] else None
		mail_handler = SMTPHandler(
			mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
			fromaddr=app.config['MAIL_USERNAME'], # this is kinda specific to mailgun...
			toaddrs=app.config['ERROR_REPORT_EMAIL'],
			subject='Darkchess Frontend Error',
			credentials=auth, secure=secure
		)
		mail_handler.setLevel(logging.ERROR)
		app.logger.addHandler(mail_handler)

	return app
