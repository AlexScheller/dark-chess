import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env.flask'))

class Config:

	SECRET_KEY = os.environ.get('SECRET_KEY') or 'f82hy8bqk4qbl0g43gb9uq4fqvdjk904j3'

	FRONTEND_ROOT = os.environ.get('FRONTEND_ROOT') or 'http://localhost:5005'

	DB_USERNAME = os.environ.get('DB_USERNAME') or 'darkchess'
	DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'darkchess'

	# Currently both host and port are both rolled up into the `DB_HOST`
	# variable.
	DB_HOST = os.environ.get('DB_HOST') or 'localhost'
	DB_NAME = os.environ.get('DB_NAME') or 'darkchess'

	DB_SSL = os.environ.get('DB_SSL') or False
	DB_SSL_CA_LOC = os.environ.get('DB_SSL_CA_LOC') or None
	DB_SSL_CLIENT_CERT_LOC = os.environ.get('DB_SSL_CLIENT_CERT_LOC') or None
	DB_SSL_CLIENT_KEY_LOC = os.environ.get('DB_SSL_CLIENT_KEY_LOC') or None

	if DB_SSL:
		DB_SSL_STRING = f'?ssl_ca={DB_SSL_CA_LOC}&ssl_key={DB_SSL_CLIENT_KEY_LOC}&ssl_cert={DB_SSL_CLIENT_CERT_LOC}'
	else:
		DB_SSL_STRING=''

	# DB_SSL_REQUIRED = os.environ.get('DB_SSL_REQUIRED') or None

	# DB_SSL_STRING = '?sslmode=require' if DB_SSL_REQUIRED else ''

	### database ###
	DATABASE_URIS = {
		'MYSQL' : f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}{DB_SSL_STRING}',
		'POSTGRES': f'postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}{DB_SSL_STRING}',
		'SQLITE' : 'sqlite:///' + os.path.join(basedir, 'app.db')
	}
	CHOSEN_DATABASE = os.environ.get('CHOSEN_DATABASE') or 'SQLITE'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = DATABASE_URIS[CHOSEN_DATABASE]

	BETA_KEYS_REQUIRED = os.environ.get('BETA_KEYS_REQUIRED') or False