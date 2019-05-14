from flask import current_app
from dark_chess_api import db
from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import and_, or_
import chess
import random
import secrets

class MatchState(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	fen = db.Column(db.String(256))

	match_id = db.Column(db.Integer, db.ForeignKey('match.id'))


class Match(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	connection_hash = db.Column(db.String(255), index=True, unique=True)

	def __init__(self):
		self.connection_hash = secrets.token_hex(
			current_app.config['MATCH_CONNECTION_HASH_BYTES']
		)
		while Match.query.filter_by(
			connection_hash=self.connection_hash
		).first() is not None:
			self.connection_hash = secrets.token_hex(
				current_app.config['MATCH_CONNECTION_HASH_BYTES']
			)


	player_white_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	player_white = db.relationship('User',
		foreign_keys='Match.player_white_id'
	)

	player_black_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	player_black = db.relationship('User',
		foreign_keys='Match.player_black_id'
	)

	is_finished = db.Column(db.Boolean, default=False)

	winning_player_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	winning_player = db.relationship('User',
		foreign_keys='Match.winning_player_id'
	)

	history = db.relationship('MatchState')

	def join(self, player):
		if not self.playing(player):
			if self.player_white is None and self.player_black is None:
				if random.randint(0, 1) == 1:
					self.player_white = player
				else:
					self.player_black = player
			elif self.player_black is None:
				self.player_black = player
			else:
				self.player_white = player
			if not self.open: # second player has joined, create initial state
				self.history.append(MatchState(fen=chess.Board().fen()))

	@hybrid_property
	def open(self):
		return self.player_white is None or self.player_black is None

	@open.expression
	def open(cls):
		return or_(cls.player_white == None, cls.player_black == None)

	@hybrid_property
	def in_progress(self):
		return not self.is_finished and not self.open

	@in_progress.expression
	def in_progress(cls):
		return and_(cls.is_finished == False, cls.open == False)

	@property
	def current_fen(self):
		return self.history[-1].fen

	###########################################################################
	# NOTE # The following functions are written very defensively. This may   #
	######## result in redundant code, but for the time being speed is less   #
	# of a concern than stability. If at a later point more efficiency is     #
	# required, and proper testing is in place to ensure match states do not  #
	# become corrupted or allow technically invalid/forbidden inputs, these   #
	# may be wrewritten to be a bit less gaurded.                             #
	###########################################################################

	def playing(self, player):
		if self.is_finished:
			return False
		return self.player_white_id == player.id or self.player_black_id == player.id

	def players_turn(self, player):
		if not self.playing(player):
			return False
		board = chess.Board(fen=self.current_fen)
		player_side = chess.BLACK if player.id == self.player_black_id else chess.WHITE
		return player_side == board.turn

	def attempt_move(self, player, uci_string):
		move = chess.Move.from_uci(uci_string)
		board = chess.Board(fen=self.current_fen)
		if self.players_turn(player) and move in board.legal_moves:
			board.push(move)
			self.history.append(MatchState(fen=board.fen()))
			# Naive game over checking for now. There are other ways the
			# game could end.
			if board.is_checkmate():
				self.is_finished = True
				self.winning_player = player
			return True
		return False

	# Some of the initial properties are mutually exclusive, and
	# could therefore be inferred from eachother, but they are
	# all left in for convienience of questioning.
	def as_dict(self):
		ret = {
			'id' : self.id,
			'connection_hash': self.connection_hash,
			'history' : [ms.fen for ms in self.history],
			'is_finished' : self.is_finished,
			'in_progress' : self.in_progress,
			'open' : self.open,
		}
		if self.in_progress:
			ret['current_fen'] = self.current_fen
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
		if self.is_finished:
			ret['winning_side'] = 'white' if self.winning_player_id == self.player_white_id else 'black'
			ret['winner'] = self.winning_player.as_dict()
		return ret