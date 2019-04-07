from flask import Flask
from config import Config

def create_app(config=Config):

	app = Flask(__name__)
	app.config.from_object(config)

	from dark_chess_app.modules.main import main
	app.register_blueprint(main)

	from dark_chess_app.modules.auth import auth
	app.register_blueprint(auth, url_prefix='/auth')

	return app