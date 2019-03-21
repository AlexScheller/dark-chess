from tests.test_prototype import PrototypeModelTestCase, auth_encode
from dark_chess_api import db
from dark_chess_api.modules.users.models import User
from dark_chess_api.modules.matches.models import Match

class MatchTestCases(PrototypeModelTestCase):

	def setUp(self):
		super().setUp()
		db.session.add_all([
			User('user1', 'password'),
			User('user2', 'password'),
			User('user3', 'password')
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
		self.assertTrue(m.open)
		self.assertFalse(m.finished)

	def test_join_match(self):
		db.session.add(Match())
		db.session.commit()
		u1, u2, u3 = User.query.get(1), User.query.get(2), User.query.get(3)
		token1 = u1.get_token()
		join_res = self.client.patch('/match/123/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.assertEqual(404, join_res.status_code)
		m = Match.query.get(1)
		self.assertIsNone(m.player_white)
		self.assertIsNone(m.player_black)
		self.assertTrue(m.open)
		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.assertEqual(200, join_res.status_code)
		m = Match.query.get(1)
		self.assertTrue(m.player_white == u1 or m.player_black == u1)
		self.assertIn(m, u1.matches)
		self.assertTrue(m.open)
		token2 = u2.get_token()
		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		m = Match.query.get(1)
		self.assertIn(m, u2.matches)
		self.assertFalse(m.open)
		token3 = u3.get_token()
		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		self.assertEqual(403, join_res.status_code)
		m = Match.query.get(1)
		self.assertFalse(m.open)
		self.assertNotIn(m, u3.matches)