import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:

	SECRET_KEY = os.environ.get('SECRET_KEY') or 'nf7tqg4io4uqF$#bvyipw323qb43buf$@Q'

	API_SCHEMA = os.environ.get('API_SCHEMA') or 'http'
	API_DOMAIN = os.environ.get('API_DOMAIN') or 'localhost'
	API_PORT = os.environ.get('API_PORT') or '5000'
	USING_API_PORT = os.environ.get('USING_API_PORT') or True
	if USING_API_PORT
		API_URL = f'{API_SCHEMA}://{API_DOMAIN}:{API_PORT}/'
	else:
		API_URL = f'{API_SCHEMA}://{API_DOMAIN}/'