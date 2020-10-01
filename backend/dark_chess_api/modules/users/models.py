from flask import current_app
from sqlalchemy import or_, and_
from dark_chess_api import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
import secrets
import pytz

class UserRelationshipType(Enum):
	FRIEND = 1
	FRIEND_REQUEST = 2
	BLOCKED = 3

class UserRelationship(db.Model):

	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	relationship_type = db.Column(db.Enum(UserRelationshipType), primary_key=True)

	related_user = db.relationship('User', foreign_keys=[related_user_id])

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

	friends = db.relationship('UserRelationship',
		primaryjoin=and_(
			UserRelationship.user_id==id,
			UserRelationship.relationship_type==UserRelationshipType.FRIEND
		)
	)

	friends_requested = db.relationship('UserRelationship',
		primaryjoin=and_(
			UserRelationship.user_id==id,
			UserRelationship.relationship_type==UserRelationshipType.FRIEND_REQUEST
		),
		secondaryjoin=and_(
			UserRelationship.related_user_id==id,
			UserRelationship.relationship_type==UserRelationshipType.FRIEND_REQUEST
		),
		backref=db.backref('friend_requests', lazy='dynamic')
	)

	# friends = db.relationship('User', secondary=user_relationship,
	# 	primaryjoin=and_(
	# 		user_relationship.c.relationship_type==UserRelationship.FRIEND,
	# 		user_relationship.c.user_id==id
	# 	),
	# 	secondaryjoin=(user_relationship.c.related_user_id==id)
	# )

	def __init__(self, username, email, password):
		self.username = username
		self.email = email
		self.set_password(password)
		from dark_chess_api.modules.stats.models import UserStatBlock
		self.stat_block = UserStatBlock()

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
			'stats': self.stat_block.as_dict()
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

	def request_friend(self, user):
		friend_request = UserRelationship(
			relationship_type=UserRelationshipType.FRIEND_REQUEST
		)
		friend_request.related_user = user
		self.friends_requested.append(friend_request)

	def add_friend(self, user):
		friendship = UserRelationship(
			relationship_type=UserRelationshipType.FRIEND
		)
		friendship.related_user = user
		self.friends.append(friendship)

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