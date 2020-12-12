import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env.flask'))

def env_to_bool(value, default=False):
	if value is None:
		return default
	val = value.lower()
	if val in ['false', 'f', 'no', 'n', '1']:
		return False
	elif val in ['true', 't', 'yes', 'y', '0']:
		return True
	return default

class Config:

	SECRET_KEY = os.environ.get('SECRET_KEY')

	FRONTEND_ROOT = os.environ.get('FRONTEND_ROOT') or 'http://localhost:5005'

	DB_USERNAME = os.environ.get('DB_USERNAME') or 'darkchess'
	DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'darkchess'

	# Currently both host and port are both rolled up into the `DB_HOST`
	# variable.
	DB_HOST = os.environ.get('DB_HOST') or 'localhost'
	DB_NAME = os.environ.get('DB_NAME') or 'darkchess'

	DB_SSL = env_to_bool(os.environ.get('DB_SSL'), False)
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

	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = env_to_bool(os.environ.get('MAIL_USE_TLS'), False)
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ERROR_REPORT_EMAIL = os.environ.get('ERROR_REPORT_EMAIL')

	BETA_KEYS_REQUIRED = env_to_bool(os.environ.get('BETA_KEYS_REQUIRED'), False)