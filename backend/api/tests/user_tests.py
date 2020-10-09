import unittest
from tests.test_prototype import PrototypeModelTestCase, auth_encode
from dark_chess_api import db
from dark_chess_api.modules.users.models import User, BetaCode

class UserTestCases(PrototypeModelTestCase):

	def test_registration_route(self):
		u = User.query.get(1)
		self.assertIsNone(u)
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password',
				'email': 'user@example.com'
			}
		)
		self.assertEqual(200, user_res.status_code)
		u = User.query.get(1)
		self.assertIsNotNone(u)
		self.assertEqual('user', u.username)
		self.assertTrue(u.check_password('password'))
		self.assertFalse(u.check_password('wordpass'))
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password',
				'email': 'user@example.com'
			}
		)
		self.assertEqual(409, user_res.status_code)
		u = User.query.get(2)
		self.assertIsNone(u)

	def test_beta_code_registration(self):
		self.app.config['BETA_KEYS_REQUIRED'] = True
		u = User.query.get(1)
		self.assertIsNone(u)
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password',
				'email': 'user@example.com'
			}
		)
		self.assertEqual(400, user_res.status_code)
		u = User.query.get(1)
		self.assertIsNone(u)
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password',
				'email': 'user@example.com',
				'beta_code': 'hello'
			}
		)
		self.assertEqual(422, user_res.status_code)
		u = User.query.get(1)
		self.assertIsNone(u)
		bc = BetaCode()
		db.session.add(bc)
		db.session.commit()
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password',
				'email': 'user@example.com',
				'beta_code': bc.code
			}
		)
		u = User.query.get(1)
		self.assertIsNotNone(u)
		user2_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user2',
				'password' : 'password',
				'email': 'user2@example.com',
				'beta_code': bc.code
			}
		)
		self.assertEqual(422, user2_res.status_code)
		u2 = User.query.get(2)
		self.assertIsNone(u2)

	def test_aquire_token(self):
		db.session.add(User('user', 'user@example.com', 'password'))
		db.session.commit()
		token_res = self.client.get('/user/auth/token',
			headers={'Authorization': f'Basic {auth_encode("user:wordpass")}'}
		)
		self.assertEqual(401, token_res.status_code)
		u = User.query.get(1)
		self.assertIsNone(u.token)
		token_res = self.client.get('/user/auth/token',
			headers={'Authorization': f'Basic {auth_encode("user:password")}'}
		)
		self.assertEqual(200, token_res.status_code)
		token_json = token_res.get_json()
		self.assertIn('token', token_json)
		token = token_json['token']
		self.assertIsNotNone(u.token)
		self.assertIsNotNone(u.get_token())
		self.assertEqual(token, u.get_token())

	def test_revoke_token(self):
		u = User('user', 'user@example.com', 'password')
		db.session.add(u)
		db.session.commit()
		token = u.get_token()
		user_res = self.client.get('/user/1',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(200, user_res.status_code)
		u.revoke_token()
		user_res = self.client.get('/user/1',
			headers={'Authorization': f'Bearer {token}'}
		)
		self.assertEqual(401, user_res.status_code)

	def test_change_password(self):
		u = User('user', 'user@example.com', 'password')
		db.session.add(u)
		db.session.commit()
		token = u.get_token()
		chg_res = self.client.patch('/user/2/auth/change-password',
			headers={'Authorization': f'Bearer {token}'},
			json={
				'current_password' : 'password',
				'new_password' : 'wordpass'
			}
		)
		self.assertEqual(404, chg_res.status_code)
		self.assertTrue(u.check_password('password'))
		self.assertFalse(u.check_password('wordpass'))
		chg_res = self.client.patch(f'/user/{u.id}/auth/change-password',
			headers={'Authorization': f'Bearer {token}'},
			json={
				'current_password' : 'wordpass',
				'new_password' : 'wordpass'
			}
		)
		self.assertEqual(403, chg_res.status_code)
		u = User.query.get(1)
		self.assertTrue(u.check_password('password'))
		self.assertFalse(u.check_password('wordpass'))
		chg_res = self.client.patch(f'/user/{u.id}/auth/change-password',
			headers={'Authorization': f'Bearer {token}'},
			json={
				'current_password' : 'password',
				'new_password' : 'wordpass'
			}
		)
		self.assertEqual(200, chg_res.status_code)
		u = User.query.get(1)
		self.assertTrue(u.check_password('wordpass'))
		self.assertFalse(u.check_password('password'))

	def test_invite_friend(self):
		u1 = User('user', 'user@example.com', 'password')
		u2 = User('user2', 'user2@example.com', 'password')
		db.session.add_all([u1, u2])
		db.session.commit()
		self.assertNotIn(u2, u1.friends_invited)
		self.assertNotIn(u1, u2.friend_invites)
		u1_token = u1.get_token()
		invite_res = self.client.post('/user/2/friend-invite',
			headers={'Authorization': f'Bearer {u1_token}'},
		)
		self.assertEqual(200, invite_res.status_code)
		self.assertIn(u2, u1.friends_invited)

	def test_accept_friend_invite(self):
		u1 = User('user', 'user@example.com', 'password')
		u2 = User('user2', 'user2@example.com', 'password')
		db.session.add_all([u1, u2])
		db.session.commit()
		u1.friends_invited.append(u2)
		db.session.commit()
		self.assertNotIn(u2, u1.friends)
		self.assertNotIn(u1, u2.friends)
		self.assertIn(u2, u1.friends_invited)
		self.assertIn(u1, u2.friend_invites)
		u2_token = u2.get_token()
		accept_invite_res = self.client.patch('/user/1/accept-friend-invite',
			headers={'Authorization': f'Bearer {u2_token}'},
		)
		self.assertEqual(200, accept_invite_res.status_code)
		self.assertIn(u2, u1.friends)
		self.assertIn(u1, u2.friends)
		self.assertNotIn(u2, u1.friends_invited)
		self.assertNotIn(u1, u2.friend_invites)