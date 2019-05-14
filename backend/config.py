import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:

	SECRET_KEY = os.environ.get('SECRET_KEY') or 'f82hy8bqk4qbl0g43gb9uq4fqvdjk904j3'

	MATCH_CONNECTION_HASH_BYTES = 16

	DB_USERNAME = os.environ.get('DB_USERNAME') or 'darkchess'
	DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'darkchess'
	DB_HOST = os.environ.get('DB_HOST') or 'localhost'
	DB_NAME = os.environ.get('DB_NAME') or 'darkchess'

	### database ###
	DATABASE_URIS = {
		'MYSQL' : f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}',
		'SQLITE' : 'sqlite:///' + os.path.join(basedir, 'app.db')
	}
	CHOSEN_DATABASE = os.environ.get('CHOSEN_DATABASE') or 'SQLITE'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = DATABASE_URIS[CHOSEN_DATABASE]