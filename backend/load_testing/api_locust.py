from locust import HttpLocust, TaskSet, task
import requests

class APIUser:

	def __init__(self, client, basic_credentials):
		self._client = client
		self._basic_credentials = basic_credentials
		self._token = None

	def login(self):
		res = self._client.get('/user/auth/token',
			auth=self._basic_credentials
		)
		self._token = res.json()['token']

	def get_open_matches(self):
		res = self._client.get('/match/open-matches',
			headers={
				'Authorization': f'Bearer {self._token}'
			}
		)

class APIUserBehavior(TaskSet):

	def on_start(self):
		self.user = APIUser(self.client, ('alex', 'password'))
		self.user.login()

	def on_stop(self):
		pass

	@task(1)
	def get_open_matches(self):
		self.user.get_open_matches()

class APIUserLocust(HttpLocust):
	task_set = APIUserBehavior
	min_wait = 5000
	max_wait = 9000