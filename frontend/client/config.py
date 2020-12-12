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

	API_SCHEMA = os.environ.get('API_SCHEMA') or 'http'
	API_DOMAIN = os.environ.get('API_DOMAIN') or 'localhost'
	API_PORT = os.environ.get('API_PORT') or '5000'
	USING_API_PORT = env_to_bool(os.environ.get('USING_API_PORT'), True)
	API_DOMAIN_AND_PORT = ''
	if USING_API_PORT != 'False':
		API_DOMAIN_AND_PORT = f'{API_DOMAIN}:{API_PORT}'
		API_ROOT = f'{API_SCHEMA}://{API_DOMAIN}:{API_PORT}'
	else:
		API_DOMAIN_AND_PORT = API_DOMAIN
		API_ROOT = f'{API_SCHEMA}://{API_DOMAIN}'

	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = env_to_bool(os.environ.get('MAIL_USE_TLS'), False)
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ERROR_REPORT_EMAIL = os.environ.get('ERROR_REPORT_EMAIL')