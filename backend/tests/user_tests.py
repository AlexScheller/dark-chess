from tests.test_prototype import PrototypeModelTestCase
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