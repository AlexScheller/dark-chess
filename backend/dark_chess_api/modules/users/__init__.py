from flask import Blueprint

users = Blueprint('users', __name__)

# cli commands

# Appends mock users to an empty database.
@users.cli.command()
def mock():
	from faker import Faker
	from dark_chess_api import db
	from dark_chess_api.modules.users.models import User
	mocker = Faker()
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
	db.session.add_all(users)
	db.session.commit()

from dark_chess_api.modules.users import endpoints