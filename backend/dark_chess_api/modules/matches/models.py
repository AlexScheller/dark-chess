from dark_chess_api import db
from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property

class MatchState(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	fen = db.Column(db.String(256))

	match_id = db.Column(db.Integer, db.ForeignKey('match.id'))


class Match(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	player_white_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	player_white = db.relationship('User',
		foreign_keys='Match.player_white_id'
	)

	player_black_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	player_black = db.relationship('User',
		foreign_keys='Match.player_black_id'
	)

	finished = db.Column(db.Boolean, default=False)

	winning_player_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	winning_player = db.relationship('User',
		foreign_keys='Match.winning_player_id'
	)

	history = db.relationship('MatchState')

	def __init__(self, player_black=None, player_white=None):
		if player_black:
			self.player_black = player_black
		if player_white:
			self.player_white = player_white

	def join(self, player):
		if self.player_white is None:
			self.player_white = player
		else:
			self.player_black = player

	@hybrid_property
	def open(self):
		return self.player_white is None or self.player_black is None

	@property
	def current_fen(self):
		return self.history[-1].fen

	def as_dict(self):
		ret = {
			'id' : self.id,
			'history' : [ms.fen for ms in self.history],
			'is_finished' : self.finished
		}
		if self.player_white is not None:
			ret['player_white'] = {
				'id' : self.player_white.id,
				'username' : self.player_white.username
			}
		if self.player_black is not None:
			ret['player_black'] = {
				'id' : self.player_black.id,
				'username' : self.player_black.username
			}
		if self.finished:
			ret['winning_side'] = 'white' if self.winning_player_id == self.player_white_id else 'black'
			ret['winner'] = self.winning_player.as_dict()
		return ret