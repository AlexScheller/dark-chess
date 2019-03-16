from tests.test_prototype import PrototypeModelTestCase, auth_encode
from dark_chess_api import db
from dark_chess_api.modules.users.models import User

class UserModelTestCases(PrototypeModelTestCase):

	def test_registration_route(self):
		u = User.query.get(1)
		self.assertIsNone(u)
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password'
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
				'password' : 'password'
			}
		)
		self.assertEqual(409, user_res.status_code)
		u = User.query.get(2)
		self.assertIsNone(u)


	def test_aquire_token(self):
		db.session.add(User('user', 'password'))
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

	def test_change_password(self):
		u = User('user', 'password')
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