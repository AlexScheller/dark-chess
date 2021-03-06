# This file contains a helpful set of cli commands. Generally speaking they
# simply wrap various shell utilities.

import os
import click

def init(app):

	from dark_chess_api.modules.users import users

	# Wraps pip freeze to deal with the 'pkg-resources=0.0.0' bug on ubuntu.
	@app.cli.command()
	def freeze():
		os.system('pip freeze > requirements.txt')
		os.system('sed -i "/pkg-resources==0.0.0/d" requirements.txt')

	# Installs from requirements file.
	@app.cli.command()
	def requirements():
		os.system('pip install -r requirements.txt')

	# Runs test suite.
	@app.cli.command()
	@click.option('--coverage', '-c', is_flag=True, default=False,
		help='Report code coverage.')
	@click.option('--html', '-h', is_flag=True, default=False,
		help='Generate browser viewable coverage report.')
	@click.option('--purge', '-p', is_flag=True, default=True,
		help='Ensure deletion of past coverage data.')
	def test(coverage, html, purge):
		if purge:
			os.system('rm .coverage')
			os.system('rm -rf htmlcov/')
		if coverage:
			os.system('coverage run -m unittest discover -s tests -p "*_tests.py" -v')
			if html:
				os.system('coverage html')
			os.system('coverage report')
		else:
			os.system('python -m unittest discover -s tests -p "*_tests.py" -v')

	# Clears out the database (by dropping all tables) and rebuilds.
	@app.cli.command()
	def clear():
		# Note that SQLite doesn't really support a lot of migration commands
		# anyway (like `alter column`) so this will probably less relevant for
		# it.
		if app.config['CHOSEN_DATABASE'] == 'SQLITE':
			os.system('rm app.db')
		else: # for now we assume MySQL or PostgreSQL
			from sqlalchemy import MetaData, create_engine
			engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
			m = MetaData()
			m.reflect(engine)
			m.drop_all(engine)
			# Alembic Version isn't a part of the metadata
		os.system('flask db upgrade')

	# Becuase migrations are tracked with version control, a subset of the cli
	# db commands are created that are garaunteed not to mess with the
	# migrations folder.
	@app.cli.group()
	def data():
		pass

	data.add_command(clear)