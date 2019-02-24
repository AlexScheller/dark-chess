import os
import click

def init(app):

	# removes the 'pkg-resources=0.0.0' bug with ubuntu
	@app.cli.command()
	def freeze():
		os.system('pip freeze > requirements.txt')
		os.system('sed -i "/pkg-resources==0.0.0/d" requirements.txt')

	# installs from requirements file
	@app.cli.command()
	def requirements():
		os.system('pip install -r requirements.txt')