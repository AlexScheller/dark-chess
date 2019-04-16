from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from dark_chess_api.modules.utilities import validation
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config=Config):

	app = Flask(__name__)
	app.config.from_object(config)

	app.endpoint_schemas = validation.load_schemas(
		os.path.abspath(os.path.dirname(__file__)) + '/static/schemas/'
	)

	db.init_app(app)
	migrate.init_app(app, db)
	socketio.init_app(app)

	from dark_chess_api.modules.errors import errors
	app.register_blueprint(errors)

	from dark_chess_api.modules.websockets import websockets
	app.register_blueprint(websockets)

	from dark_chess_api.modules.users import users
	app.register_blueprint(users, url_prefix='/user')

	from dark_chess_api.modules.matches import matches
	app.register_blueprint(matches, url_prefix='/match')

	from dark_chess_api.modules.docs import docs
	app.register_blueprint(docs, url_prefix='/docs')

	return app