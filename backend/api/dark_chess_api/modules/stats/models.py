import random

from dark_chess_api import db

class UserStatBlock(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	### intrinsic ###
	games_played = db.Column(db.Integer, default=0)
	games_won = db.Column(db.Integer, default=0)
	games_lost = db.Column(db.Integer, default=0)
	games_tied = db.Column(db.Integer, default=0)
	rating = db.Column(db.Integer)

	### relationship ###
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user = db.relationship('User', back_populates='stat_block')

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