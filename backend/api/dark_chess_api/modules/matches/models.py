import chess
import random
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import and_, or_
from flask import current_app

from dark_chess_api import db

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

	def king_captured(self):
		return self.king(self.turn) is None

# TODO: Configure the join to load eagerly
class MatchInvite(db.Model):
	
	id = db.Column(db.Integer, primary_key=True)

	inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	inviter = db.relationship('User', foreign_keys='MatchInvite.inviter_id')

	invited_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	invited = db.relationship('User', foreign_keys='MatchInvite.invited_id')

	match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
	match = db.relationship('Match')

	created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	def __init__(self, inviter, invited=None):
		self.inviter = inviter
		self.invited = invited

	@hybrid_property
	def open(self):
		return self.invited_id is None

	@open.expression
	def open(cls):
		return cls.invited_id == None

	@hybrid_property
	def accepted(self):
		return self.match_id is not None

	@accepted.expression
	def accepted(cls):
		return cls.match_id != None

	@staticmethod
	def mock_dict(force_direct=False, force_accepted=False):
		created_on = datetime.now(timezone.utc)
		from dark_chess_api.modules.users.models import User

		mock_inviter = User.mock_dict()
		mock_invited = None
		if force_direct or random.choice([True, False]):
			mock_invited = User.mock_dict()
		match_id = None
		if (force_accepted or random.choice([True, False])) and mock_invited is not None:
			match_id = random.randint(1, 100)
		ret = {
			'id': random.randint(1, 100),
			'inviter': {
				'id': mock_inviter['id'],
				'username': mock_inviter['username']
			},
			'open': mock_invited is None,
			'accepted': match_id is not None,
			'created_on': {
				'formatted': str(created_on),
				'timestamp': int(created_on.timestamp())
			}
		}
		if mock_invited is not None:
			ret.update({
				'invited': {
					'id': mock_invited['id'],
					'username': mock_invited['username']
				}
			})
		if match_id is not None:
			ret.update({
				'match_id': match_id 
			})
		return ret

	def as_dict(self):
		ret = {
			'id': self.id,
			'inviter': {
				'id': self.inviter.id,
				'username': self.inviter.username
			},
			'open': self.open,
			'accepted': self.accepted,
			'created_on': {
				'formatted': str(self.created_on),
				'timestamp': int(self.created_on.timestamp())
			}
		}
		if self.invited_id is not None:
			ret.update({
				'invited': {
					'id': self.invited.id,
					'username': self.invited.username
				}
			})
		if self.match_id is not None:
			ret.update({
				'match_id': self.match_id 
			})
		return ret

class MatchState(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	fen = db.Column(db.String(256), nullable=False)

	match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)

class Match(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	connection_token = db.Column(db.String(36), index=True, unique=True, nullable=False)

	def __init__(self):
		self.connection_token = str(uuid4())

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

	@staticmethod
	def expand_fen(fen):
		ret = []
		positions = fen.split(' ')[0].split('/')
		for row in positions:
			new_row = [
				square if square.isalpha() else '_' * int(square)
				for square in row
			]
			ret.append(''.join(new_row))
		return '/'.join(ret)

	@property
	def current_expanded_fen(self):
		board = chess.Board(fen=self.current_fen)
		ret = ''
		# chess.py conceives of boards as being a1 -> h8 with white on top, but
		# we use the traditional method of a8 -> h1 with black on top. Because
		# of this, we iterate through the ranks in reverse.
		for rank in range(7, -1, -1):
			for file in range(8):
				square = chess.square(file, rank)
				piece = board.piece_at(square)
				ret += piece.symbol() if piece is not None else '_'
			if rank > 0:
				ret += '/'
		return ret

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

	def has_player(self, player):
		return self.player_black_id == player.id or self.player_white_id == player.id

	def playing(self, player):
		return False if self.is_finished else self.has_player(player)

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
		board = DarkBoard(fen=self.current_fen)
		if self.players_turn(player) and move in board.pseudo_legal_moves:
			board.push(move)
			self.history.append(MatchState(fen=board.fen()))
			if board.is_checkmate() or board.king_captured():
				self.is_finished = True
				self.winning_player = player
			return True
		return False

	@staticmethod
	def mock_dict(side=None, game_state=None):
		# Avoids circular import issue.
		from dark_chess_api.modules.users.models import User

		mock_player_black = None
		mock_player_white = None
		mock_open = False
		mock_finished = False
		mock_in_progress = False

		if game_state is not None and game_state in ['open', 'in_progress', 'finished']:
			if game_state == 'open':
				mock_open = True
				if random.choice([True, False]):
					mock_player_black = User.mock_dict()
				else:
					mock_player_white = User.mock_dict()
			elif game_state == 'in_progress':
				mock_in_progress = True
			elif game_state == 'finished':
				mock_finished = True
		else:
			mock_open = random.choice([True, False, False, False])
			mock_in_progress = False if mock_open else random.choice([True, False])
			mock_finished = not (mock_in_progress or mock_open)
		if mock_in_progress or mock_finished:
			mock_player_black = User.mock_dict()
			mock_player_white = User.mock_dict()
			if side is None:
				side = random.choice(['white', 'black', 'spectating'])
		ret = {
			'id' : random.randint(1, 100),
			'is_finished' : mock_finished,
			'in_progress' : mock_in_progress,
			'open' : mock_open,
			'player_black': {
				'id': mock_player_black['id'],
				'username': mock_player_black['username']
			} if mock_player_black is not None else None,
			'player_white': {
				'id': mock_player_white['id'],
				'username': mock_player_white['username']
			} if mock_player_white is not None else None
		}
		if side is not None or mock_open:
			ret.update({
				'connection_token': '[connection hash/token]'
			})
		if side == 'spectating':
			ret.update({
				'transparent_history': '[An array of fens representing the history of the match.]'
			})
		else:
			ret.update({
				f'{side}_vision_history': '[An array of dark fens representing the history of the match]'
			})
		if mock_in_progress:
			# Hard code the current player so that we can hard code the fen.
			# Not gunna spend time yet randomly generating a game. The fen
			# selected comes from https://www.chess.com/terms/fen-chess
			ret.update({
				'current_side': 'black',
				'current_player_id': mock_player_black['id']
			})
			if side is not None:
				if side != 'spectating':
					mock_dark_fen = None
					if side == 'white':
						mock_dark_fen = '?_??k_??/??_?_?N?/?_?B__?_/_p?NP__P/?_?___P?/_?_P_Q__/P?P_K__?/???___?_'
					else:
						mock_dark_fen = 'r_b_k_nr/p__p_p?p/n_???_?_/_p_?P???/__?_????/_?_?_???/__???_?_/q_____b?'
					ret.update({
						'current_dark_fen': mock_dark_fen,
						'possible_moves': '[An object with origin squares as keys, and arrays of subsequent destination squares as values.]'
					})
				else:
					ret.update({
						'current_fen': 'r_b_k_nr/p__p_pNp/n__B____/_p_NP__P/______P_/___P_Q__/P_P_K___/q_____b_',
					})
		elif mock_finished:
			# Same deal as the in progress game with a Fool's mate.
			ret.update({
				'winning_side': 'black',
				'current_fen': 'rnb_kbnr/pppp_ppp/________/____p___/______Pq/_____P__/PPPPP__P/RNBQKBNR',
				'winner': mock_player_black
			})
		return ret

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
				'connection_token': self.connection_token
			})
		if side == 'spectating':
			ret.update({
				'transparent_history': [Match.expand_fen(ms.fen) for ms in self.history]
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
						'current_fen': self.current_expanded_fen,
					})
		if self.is_finished:
			ret.update({
				'winning_side': 'white' if self.winning_player_id == self.player_white_id else 'black',
				'current_fen': self.current_expanded_fen,
				'winner': self.winning_player.as_dict()
			})
		return ret