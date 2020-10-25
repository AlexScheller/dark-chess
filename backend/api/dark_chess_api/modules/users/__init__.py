import click
from flask import Blueprint

users = Blueprint('users', __name__)

# cli commands

# Appends mock users to an empty database.
@users.cli.command()
def mock():
	from dark_chess_api import db, mocker
	from dark_chess_api.modules.users.models import User
	# users
	users = []
	seen_name_counts = {}
	for i in range(20):
		username = mocker.name().replace(' ', '')
		# Yes this is a tad overcautious but in testing with insertion of
		# 1000 users, 5 were double dups and 3 were triple dups, so it
		# certainly can happen in non-massive datasets. Rather check here
		# than have the unique constraint yell at me at random times.
		if username in seen_name_counts:
			seen_name_counts[username] += 1
			username = f'{username}{seen_name_counts[username]}'
		else:
			seen_name_counts[username] = 1
		u = User(username, f'{username.lower()}@example.com', 'password')
		users.append(u)
	# Include a couple of hardcoded ones to rely on
	users.append(User('alex', 'alex@example.com', 'password'))
	users.append(User('maya', 'maya@examplecom', 'password'))
	db.session.add_all(users)
	db.session.commit()

# Gens up a fresh batch of unused beta codes. This should be removed once the
# invite-only period is over.
@users.cli.command()
@click.option('-c', '--count', default=1, help='Number of beta codes to generate.')
@click.option('-s', '--silent', is_flag=True)
def betagen(count, silent):
	from dark_chess_api import db
	from dark_chess_api.modules.users.models import BetaCode
	new_codes = [BetaCode() for i in range(count)]
	db.session.add_all(new_codes)
	db.session.commit()
	if not silent:
		for code in new_codes:
			print(code.code)

from dark_chess_api.modules.users import endpoints