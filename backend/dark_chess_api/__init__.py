from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config=Config):

	app = Flask(__name__)
	app.config.from_object(config)

	db.init_app(app)
	migrate.init_app(app, db)

	from dark_chess_api.modules.errors import errors
	app.register_blueprint(errors)

	from dark_chess_api.modules.users import users
	app.register_blueprint(users, url_prefix='/user')

	return app