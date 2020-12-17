import random

from dark_chess_api import db

class UserStatBlock(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	### intrinsic ###
	games_played = db.Column(db.Integer, default=0)
	games_won = db.Column(db.Integer, default=0)
	games_lost = db.Column(db.Integer, default=0)
	# Is this really even possible?
	games_tied = db.Column(db.Integer, default=0)
	rating = db.Column(db.Integer)

	### relationship ###
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user = db.relationship('User', back_populates='stat_block')

	# TODO: Perhaps this should extend the __add__ method?
	def add_match(self, match):
		# These two checks may be an unnecessary performance burden.
		if not match.is_finished:
			raise ValueError('Match not finished')
		if not match.has_player(self.user):
			raise ValueError('Player not in match')
		self.games_played += 1
		if match.winning_player_id == self.user.id:
			self.games_won += 1
		else:
			self.games_lost += 1

	@staticmethod
	def mock_dict():
		games = random.randint(0, 1000)
		if games > 0:
			won = random.randint(0, games)
			lost = games - won
		else:
			won, lost = 0, 0
		return {
			'games': {
				'played': games,
				'won': won,
				'lost': lost,
				'tied': 0 # lazy of me yeah
			},
			'rating': random.randint(500, 2000)
		}

	def as_dict(self):
		return {
			'games': {
				'played': self.games_played,
				'won': self.games_won,
				'lost': self.games_lost,
				'tied': self.games_tied
			},
			'rating': self.rating
		}