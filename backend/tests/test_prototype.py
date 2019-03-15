from dark_chess_api import create_app, db
from config import Config
import unittest

# Another file that borrows heavily from Miguel Grinberg's Microblog

class TestConfig(Config):
	TESTING = True
	SQL_ALCHEMY_DATABASE_URI = 'sqlite://'

class PrototypeModelTestCase(unittest.TestCase):

	def setUp(self):
		self.app = create_app(TestConfig)
		self.client = self.app.test_client()
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()