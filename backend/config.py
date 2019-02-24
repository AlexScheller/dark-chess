import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:

	SECRET_KEY = os.environ.get('SECRET_KEY') or 'f82hy8bqk4qbl0g43gb9uq4fqvdjk904j3'

	### database ###
	DATABASE_URIS = {
		'SQLITE' : 'sqlite:///' + os.path.join(basedir, 'app.db')
	}
	CHOSEN_DATABASE = os.environ.get('CHOSEN_DATABASE') or 'SQLITE'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = DATABASE_URIS[CHOSEN_DATABASE]