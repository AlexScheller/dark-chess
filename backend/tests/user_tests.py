from tests.test_prototype import PrototypeModelTestCase

class UserModelTestCase(PrototypeModelTestCase):

	def test_registration_route(self):
		user_res = self.client.post('/user/auth/register',
			json={
				'username' : 'user',
				'password' : 'password'
			}
		)
		self.assertEqual(200, user_res.status_code)