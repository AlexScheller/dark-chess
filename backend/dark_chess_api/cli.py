# This file contains a helpful set of cli commands. Generally speaking
# they simply wrap various shell utilities.

import os
import click

def init(app):

	# Deletes and rebuild the database from scratch. For now this is about as
	# naive as things can get, however it's only meant for development.
	@app.cli.command()
	def rebuilddb():
		os.system('rm -rf migrations/')
		if app.config['CHOSEN_DATABASE'] == 'SQLITE':
			os.system('rm app.db')
		elif app.config['CHOSEN_DATABASE'] in ['POSTGRESQL', 'MYSQL'] :
			from sqlalchemy import MetaData, create_engine
			engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
			m = MetaData()
			m.reflect(engine)
			m.drop_all(engine)
		os.system('flask db init')
		os.system('flask db migrate')
		os.system('flask db upgrade')

	# removes the 'pkg-resources=0.0.0' bug with ubuntu
	@app.cli.command()
	def freeze():
		os.system('pip freeze > requirements.txt')
		os.system('sed -i "/pkg-resources==0.0.0/d" requirements.txt')

	# installs from requirements file
	@app.cli.command()
	def requirements():
		os.system('pip install -r requirements.txt --upgrade')

	#runs test suite
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