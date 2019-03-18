from tests.test_prototype import PrototypeModelTestCase, auth_encode
from dark_chess_api import db
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.matches.models import Match

class MatchTestCases(PrototypeModelTestCase):

	def setUp(self):
		super().setUp()
		db.session.add_all([
			User('user1', 'password'),
			User('user2', 'password')
		])
		db.session.commit()

	def test_create_match(self):
		u = User.query.get(1)
		token = u.get_token()
		create_res = self.client.post('/match/create',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(200, create_res.status_code)
		m = Match.query.get(1)
		self.assertIsNotNone(m)
