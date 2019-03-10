# This file contains a helpful set of cli commands. Generally speaking
# they simply wrap various shell utilities.

import os
import click

def init(app):

	# deletes and rebuild the database from scratch
	@app.cli.command()
	def rebuilddb():
		if app.config['CHOSEN_DATABASE'] == 'SQLITE':
			os.system('rm app.db')
			os.system('rm -rf migrations/')
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