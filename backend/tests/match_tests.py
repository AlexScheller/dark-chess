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
		self.assertFalse(m.is_finished)

	def test_get_match(self):
		db.session.add(Match())
		db.session.commit()
		u = User.query.get(1)
		token = u.get_token()
		match_res = self.client.get('/match/123',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(404, match_res.status_code)
		match_res = self.client.get('/match/1',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(200, match_res.status_code)
		match_json = match_res.get_json()
		self.assertEqual(1, match_json['id'])

	def test_get_open_matches(self):
		for i in range(5):
			db.session.add(Match())
			db.session.flush()
		db.session.commit()
		m2, m4 = Match.query.get(2), Match.query.get(4)
		u1, u2 = User.query.get(1), User.query.get(2)
		m2.join(u1)
		m2.join(u2)
		m4.join(u1)
		m4.join(u2)
		db.session.commit()
		self.assertFalse(m2.open)
		self.assertFalse(m4.open)
		token = u1.get_token()
		open_matches_res = self.client.get('/match/open-matches',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(200, open_matches_res.status_code)
		open_matches_json = open_matches_res.get_json()
		for match_id in open_matches_json:
			m = Match.query.get(match_id)
			self.assertTrue(m.open)

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
		self.assertFalse(m.in_progress)

		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.assertEqual(200, join_res.status_code)
		m = Match.query.get(1)
		self.assertTrue(m.playing(u1))
		self.assertIn(m, u1.matches)
		self.assertTrue(m.open)
		self.assertFalse(m.in_progress)

		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.assertEqual(409, join_res.status_code)
		m = Match.query.get(1)
		self.assertTrue(m.open)
		self.assertFalse(m.in_progress)

		token2 = u2.get_token()
		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		self.assertEqual(200, join_res.status_code)
		m = Match.query.get(1)
		self.assertIn(m, u2.matches)
		self.assertFalse(m.open)
		self.assertTrue(m.in_progress)
		if m.player_white == u2:
			self.assertTrue(m.players_turn(u2))
		else:
			self.assertTrue(m.players_turn(u1))

		token3 = u3.get_token()
		join_res = self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		self.assertEqual(403, join_res.status_code)
		m = Match.query.get(1)
		self.assertFalse(m.open)
		self.assertNotIn(m, u3.matches)
		self.assertFalse(m.playing(u3))
		self.assertFalse(m.players_turn(u3))

	def test_attempt_move(self):
		db.session.add(Match())
		db.session.commit()
		u1, u2, u3 = User.query.get(1), User.query.get(2), User.query.get(3)
		token1 = u1.get_token()
		token2 = u2.get_token()
		token3 = u3.get_token()
		self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		m = Match.query.get(1)
		self.assertTrue(m.in_progress)
		if m.players_turn(u1):
			playing_token = token1
			not_playing_token = token2
		else:
			playing_token = token2
			not_playing_token = token1
		move_res = self.client.post('/match/1/make-move',
			headers={'Authorization': f'Bearer {token3}'},
			json={
				'uci_string': 'e2e4'
			}
		)
		self.assertEqual(403, move_res.status_code)
		m = Match.query.get(1)
		self.assertEqual(1, len(m.history))

		move_res = self.client.post('/match/1/make-move',
			headers={'Authorization': f'Bearer {not_playing_token}'},
			json={
				'uci_string': 'hello'
			}
		)
		self.assertEqual(400, move_res.status_code)
		m = Match.query.get(1)
		self.assertEqual(1, len(m.history))

		move_res = self.client.post('/match/1/make-move',
			headers={'Authorization': f'Bearer {not_playing_token}'},
			json={
				'uci_string': 'e2e4'
			}
		)
		self.assertEqual(409, move_res.status_code)
		m = Match.query.get(1)
		self.assertEqual(1, len(m.history))

		move_res = self.client.post('/match/1/make-move',
			headers={'Authorization': f'Bearer {playing_token}'},
			json={
				'uci_string': 'e2e5'
			}
		)
		self.assertEqual(422, move_res.status_code)
		m = Match.query.get(1)
		self.assertEqual(1, len(m.history))

		move_res = self.client.post('/match/1/make-move',
			headers={'Authorization': f'Bearer {playing_token}'},
			json={
				'uci_string': 'e2e4'
			}
		)
		self.assertEqual(200, move_res.status_code)
		m = Match.query.get(1)
		self.assertEqual(2, len(m.history))

	def test_finish_match(self):
		db.session.add(Match())
		db.session.commit()
		u1, u2 = User.query.get(1), User.query.get(2)
		fools_mate = ['f2f3', 'e7e5', 'g2g4', 'd8h4']
		token1 = u1.get_token()
		token2 = u2.get_token()
		self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token1}'}
		)
		self.client.patch('/match/1/join',
			headers={'Authorization': f'Bearer {token2}'}
		)
		m = Match.query.get(1)
		if m.players_turn(u1):
			player_white = u1
			player_black = u2
		else:
			player_white = u2
			player_black = u1
		for i in range(len(fools_mate)):
			if i % 2 == 0:
				playing_token = player_white.get_token()
			else:
				playing_token = player_black.get_token()
			self.client.post('/match/1/make-move',
				headers={'Authorization': f'Bearer {playing_token}'},
				json={
					'uci_string': fools_mate[i]
				}
			)
		m = Match.query.get(1)
		self.assertTrue(m.is_finished)
		self.assertFalse(m.in_progress)
		self.assertFalse(m.playing(u1))
		self.assertFalse(m.playing(u2))