import pytz
import random
import secrets
from uuid import uuid4
from enum import Enum
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash

from dark_chess_api import db, mocker

# Yes these three relationships could be configured to reside in a single table
# with a discriminant Enum column or something, but that only really saves us
# time if we plan on adding significantly more relationships. This model is more
# explicit and likely more performant.

user_friend = db.Table('user_friend',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

user_friend_invite = db.Table('user_friend_invite',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('invited_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)
 
class User(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	### account information data ###
	username = db.Column(db.String(255), index=True, unique=True)
	email = db.Column(db.String(255), index=True, unique=True)
	email_confirmed = db.Column(db.Boolean, default=False)
	registration_date = db.Column(db.DateTime, default=datetime.utcnow)

	### auth data ###
	password_hash = db.Column(db.String(255))
	# token auth model taken from "microblog" (see README.md)
	token = db.Column(db.String(64), index=True, unique=True)
	token_expiration = db.Column(db.DateTime)

	matches = db.relationship('Match',
		primaryjoin='or_('
			'Match.player_white_id==User.id,'
			'Match.player_black_id==User.id'
		')'
	)

	stat_block = db.relationship('UserStatBlock', uselist=False, back_populates='user')

	friends = db.relationship('User', secondary=user_friend,
		primaryjoin=(user_friend.c.user_id==id),
		secondaryjoin=(user_friend.c.friend_id==id)
	)

	friends_invited = db.relationship('User', secondary=user_friend_invite,
		primaryjoin=(user_friend_invite.c.user_id==id),
		secondaryjoin=(user_friend_invite.c.invited_id==id),
		backref=db.backref('friend_invites')
	)

	def __init__(self, username, email, password):
		self.username = username
		self.email = email
		self.set_password(password)
		# Avoids circular import issue.
		from dark_chess_api.modules.stats.models import UserStatBlock
		self.stat_block = UserStatBlock()

	@staticmethod
	def mock_dict():
		username = username = mocker.name().replace(' ', '')
		registration_date = datetime.now(timezone.utc)
		# Avoids circular import issue.
		from dark_chess_api.modules.stats.models import UserStatBlock
		return {
			'id': random.randint(1, 100),
			'username': username,
			'email': f'{username.lower()}@example.com',
			'email_confirmed': random.choice([True, False]),
			'registration_date': {
				'formatted': str(registration_date),
				'timestamp': int(registration_date.timestamp())
			},
			'stats': UserStatBlock.mock_dict(),
			'friends': [
				{
					'username': mocker.name().replace(' ', ''),
					'id': random.randint(1, 100)
				} for i in range(random.randint(0, 4))
			]
		}

	### account information methods ###
	def as_dict(self):
		return {
			'id' : self.id,
			'username' : self.username,
			'email': self.email,
			'email_confirmed': self.email_confirmed,
			'registration_date' : {
				'formatted' : str(self.registration_date),
				'timestamp' : int(self.registration_date.replace(tzinfo=pytz.utc).timestamp())
			},
			'stats': self.stat_block.as_dict(),
			'friends': [
				{
					'username': f.username,
					'id': f.id
				} for f in self.friends
			]
		}

	### auth methods ###
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def get_token(self, lifespan_seconds=7200):
		now = datetime.utcnow()
		# if there is no token, or if the token is less than a minute from
		# expiring, generate a new one.
		if not self.token or self.token_expiration < now + timedelta(seconds=60):
			self.token = secrets.token_hex(32)
			self.token_expiration = now + timedelta(seconds=lifespan_seconds)
			db.session.add(self)
			db.session.commit()
		return self.token

	def revoke_token(self):
		self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

	@staticmethod
	def get_with_token(token):
		user = User.query.filter_by(token=token).first()
		if user is None or user.token_expiration < datetime.utcnow():
			return None
		return user

	def invite_friend(self, user):
		self.friends_invited.append(user)

	def accept_friend(self, user):
		self.friends.append(user)
		user.friends.append(self)
		user.friends_invited.remove(self)

# Facilitiates the invite-only period of the application. This should be removed
# once that period is over.
user_beta_code = db.Table('user_beta_code',
	db.Column('id', db.Integer, primary_key=True),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
	db.Column('beta_code_id', db.String(36), db.ForeignKey('beta_code.id'), nullable=False)
)

# Facilitiates the invite-only period of the application. This should be removed
# once that period is over. To make that easier, no code dealing with beta codes
# should be added to the user model directly.
class BetaCode(db.Model):

	id = db.Column(db.String(36), primary_key=True)

	user = db.relationship('User', secondary=user_beta_code, uselist=False)

	def __init__(self):
		self.id = str(uuid4())

	@property
	def code(self):
		return self.id