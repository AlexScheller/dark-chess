from dark_chess_api import db
from sqlalchemy import and_
from dark_chess_api.modules.users.models import User
from sqlalchemy.ext.hybrid import hybrid_property

match_player = db.Table('match_player',
	db.Column('match_id', db.Integer, db.ForeignKey('match.id')),
	db.Column('player_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('player_is_white', db.Boolean)
)

class MatchState(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	fen = db.Column(db.String(256))

	match_id = db.Column(db.Integer, db.ForeignKey('match.id'))

class Match(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	player_white = db.relationship('User',
		secondary=match_player,
		primaryjoin=(match_player.c.match_id==id),
		secondaryjoin=and_(
			match_player.c.player_id==User.id,
			match_player.c.player_is_white==True
		),
		uselist=False
	)

	player_black = db.relationship('User',
		secondary=match_player,
		primaryjoin=(match_player.c.match_id==id),
		secondaryjoin=and_(
			match_player.c.player_id==User.id,
			match_player.c.player_is_white==False
		),
		uselist=False
	)

	# _winning_player_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	finished = db.Column(db.Boolean, default=False)

	history = db.relationship('MatchState')

	# def join(self, player):
	# 	if self.player_white is None:
	# 		self.player_white = player
	# 	else:
	# 		self.player_black = player

	def join(self, player):
		ins = match_player.insert().values(
			player_id=player.id,
			match_id=self.id,
			player_is_white=(self.player_white is None)
		)
		db.engine.execute(ins)

	@hybrid_property
	def open(self):
		return self.player_white is None or self.player_black is None

	@property
	def current_fen(self):
		return self.history[-1].fen

	@property
	def winner(self):
		if self.finished:
			if self._winning_player_id == self._player_black_id:
				return self.player_black
			return self.player_white
		return None

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
			ret['winning_side'] : 'white' if self._winning_player_id == self._player_white_id else 'black'
		return ret