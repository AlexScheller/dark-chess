from flask import Blueprint

matches = Blueprint('matches', __name__)

# cli commands

# Creates a list of mock matches. For now these are all open matches, but in
# the future should include matches mid play.
@matches.cli.command()
def mock():
	from dark_chess_api import db
	from dark_chess_api.modules.users.models import User
	from dark_chess_api.modules.matches.models import Match
	for user in User.query.all():
		match = Match()
		db.session.add(match)
		match.join(user)
		db.session.flush()
	db.session.commit()

from dark_chess_api.modules.matches import models, endpoints