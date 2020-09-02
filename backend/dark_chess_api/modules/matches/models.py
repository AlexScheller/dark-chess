from flask import current_app
from dark_chess_api import db
from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import and_, or_
import chess
import random
import secrets

# Note that this file is full of inneficient code, most notably many
# instantiations of board objects for simple functions. In the future this may
# be made more efficient, but currently development time is prioritized, as
# projected actual usage (that is, http requests) is super low.

# This helper class encapsulates the chess.py board and provides some darkchess
# specific utility functions.
# TODO: Convert most (all?) calls to `chess.Board` to use this class instead.
class DarkBoard(chess.Board):

	def dark_fen(self, side):
		player_side = chess.WHITE if side == 'white' else chess.BLACK
		# We swap the board to the requesting side so that it can render the
		# proper vision from `self.pseudo_legal_moves`
		self.turn = player_side
		attackable_squares = []
		for move in self.pseudo_legal_moves:
			attackable_squares.append(move.from_square)
			attackable_squares.append(move.to_square)
		dfen = ''
		# chess.py conceives of boards as being a1 -> h8 with white on top, but
		# we use the traditional method of a8 -> h1 with black on top. Because
		# of this, we iterate through the ranks in reverse.
		for rank in range(7, -1, -1):
			for file in range(8):
				square = chess.square(file, rank)
				piece = self.piece_at(square)
				if (square in attackable_squares or
					(piece is not None and piece.color == player_side)):
					dfen += piece.symbol() if piece is not None else '_'
				else:
					dfen += '?'
			if rank > 0:
				dfen += '/'
		return dfen

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

	is_finished = db.Column(db.Boolean, default=False, nullable=False)

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
	def current_player(self):
		if not self.in_progress:
			return None
		board = chess.Board(fen=self.current_fen)
		return self.player_white if (board.turn == chess.WHITE) else self.player_black

	@property
	def current_fen(self):
		return self.history[-1].fen

	def current_dark_fen(self, side):
		if not self.in_progress:
			return None
		return self.current_board(side).dark_fen(side)
		# This is kept for a while, but this will longer be cliffhanger dark.
		# if side == self.current_side:
		# 	return self.current_board(side).dark_fen(side)
		# # In cliffhanger dark, you don't see the results of your move until it's
		# # your turn again, so we return the fen from one move ago, not the
		# # actual current fen.
		# if len(self.history) >= 2:
		# 	return DarkBoard(fen=self.history[-2].fen).dark_fen(side)
		# return (
		# 	'????????/????????/????????/????????/'
		# 	'????????/????????/????????/????????'
		# )

	# @property
	# def current_board(self):
	# 	if not self.in_progress:
	# 		return None
	# 	return chess.Board(fen=self.current_fen)

	def current_board(self, side):
		if not self.in_progress:
			return None
		return DarkBoard(fen=self.current_fen)

	@property
	def current_side(self):
		if not self.in_progress:
			return None
		white = chess.Board(fen=self.current_fen).turn
		return 'white' if white else 'black'

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

	# def player_side(self, player):
	# 	if not self.playing(player):
	# 		return None
	# 	return 'w'

	# Note that be cause this is dark chess, the list of moves includes pseudo-
	# legal ones, such as moves that leave the king in check.
	def possible_moves(self, side):
		if not self.in_progress:
			return {}
		if self.current_side != side:
			return {}
		moves = self.current_board(side).pseudo_legal_moves
		# List comprehensions may be nicer to look at here, but would be less
		# performant
		ret = {}
		for move in moves:
			if move.from_square in ret:
				ret[move.from_square].append(move.to_square)
			else:
				ret[move.from_square] = [move.to_square]
		return ret

	def possible_moves_as_names(self, side):
		return {
			chess.SQUARE_NAMES[move_from]: [
				chess.SQUARE_NAMES[move_to] for move_to in moves_to
			]
			for move_from, moves_to in self.possible_moves(side).items()
		}

	def attempt_move(self, player, uci_string):
		move = chess.Move.from_uci(uci_string)
		board = chess.Board(fen=self.current_fen)
		if self.players_turn(player) and move in board.pseudo_legal_moves:
			board.push(move)
			self.history.append(MatchState(fen=board.fen()))
			# Naive game over checking for now. There are other ways the
			# game could end.
			if board.is_checkmate():
				self.is_finished = True
				self.winning_player = player
			return True
		return False

	# Some of the initial properties are mutually exclusive, and could
	# therefore be inferred from eachother, but they are all left in for
	# convienience of questioning. This whole method probably should be
	# refactored.
	def as_dict(self, side=None):
		ret = {
			'id' : self.id,
			'is_finished' : self.is_finished,
			'in_progress' : self.in_progress,
			'open' : self.open,
			'player_black': {
				'id': self.player_black.id,
				'username': self.player_black.username
			} if self.player_black is not None else None,
			'player_white': {
				'id': self.player_white.id,
				'username': self.player_white.username
			} if self.player_white is not None else None
		}
		# I guess it doesn't really matter to hide the connection hash ever,
		# since until the match is full it's fully exposed and anyone can copy
		# it or scrape it or whatever. TODO: Think about this one some more.
		if side is not None or self.open:
			ret.update({
				'connection_hash': self.connection_hash
			})
		if side == 'spectating':
			ret.update({
				'transparent_history': [ms.fen for ms in self.history]
			})
		else:
			ret.update({
				f'{side}_vision_history': [
					DarkBoard(fen=ms.fen).dark_fen(side) for ms in self.history
				]
			})
		if self.in_progress:
			ret.update({
				'current_side': self.current_side,
				'current_player_id': self.current_player.id
			})
			if side is not None:
				if side != 'spectating':
					ret.update({
						'current_dark_fen': self.current_dark_fen(side),
						'possible_moves': self.possible_moves_as_names(side)
					})
				else:
					ret.update({
						'current_fen': self.current_fen,
					})
		if self.is_finished:
			ret.update({
				'winning_side': 'white' if self.winning_player_id == self.player_white_id else 'black',
				'winner': self.winning_player.as_dict()
			})
		return ret