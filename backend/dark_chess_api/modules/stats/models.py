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