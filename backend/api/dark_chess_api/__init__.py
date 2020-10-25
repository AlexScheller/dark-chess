import os
from faker import Faker

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_talisman import Talisman

from config import Config
from dark_chess_api.endpoint_handler import EndpointHandler

##############
#  Services  #
##############

db = SQLAlchemy() # database
migrate = Migrate() # database migrations
socketio = SocketIO() # web-sockets
talisman = Talisman() # security-defaults
mocker = Faker() # mocking service
endpoint = EndpointHandler() # endpoint validation and documentation

def create_app(config=Config):

	app = Flask(__name__)
	app.config.from_object(config)

	from dark_chess_api.modules.utilities import validation
	app.endpoint_schemas = validation.load_schemas(
		os.path.abspath(os.path.dirname(__file__)) + '/static/schemas/'
	)

	from dark_chess_api.modules.errors.handlers import error_response
	endpoint.init_app(app, error_handler=error_response)

	CORS(app, resources={'/socket.io/': {'origins': app.config['FRONTEND_ROOT']}})
	db.init_app(app)
	migrate.init_app(app, db)
	socketio.init_app(app, cors_allowed_origins=app.config['FRONTEND_ROOT'])
	# we will enforce https upstream with nginx
	talisman.init_app(app,
		force_https=False
	)

	from dark_chess_api.modules.errors import errors
	app.register_blueprint(errors)

	from dark_chess_api.modules.websockets import websockets
	app.register_blueprint(websockets)

	from dark_chess_api.modules.users import users
	app.register_blueprint(users, url_prefix='/user')

	from dark_chess_api.modules.stats import stats
	app.register_blueprint(stats, url_prefix='/stats')

	from dark_chess_api.modules.matches import matches
	app.register_blueprint(matches, url_prefix='/match')

	from dark_chess_api.modules.docs import docs
	app.register_blueprint(docs, url_prefix='/docs')

	return app
