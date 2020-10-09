from dark_chess_app import login
from flask_login import UserMixin

# Note that this is a temporary solution to storing user sessions.
# it has the distinct disadvatage that it cannot be shared by
# multiple processes/servers. Sooner rather than later this should
# probably be refactored to make use of redis or something.
users = {}

@login.user_loader
def load_user(token):
	return users[token] if token in users else None

class User(UserMixin):

	def __init__(self, token, user_data):
		# update the session manager
		self.token = token
		users[token] = self
		# Cache user data
		self.id = user_data['id']
		self.username = user_data['username']
		self.email_confirmed = user_data['email_confirmed']
		self.registration_timestamp = user_data['registration_date']['timestamp']
		self.friends = user_data['friends']

	def get_id(self):
		return self.token

	def as_dict(self):
		return {
			'id' : self.id,
			'username' : self.username,
		}