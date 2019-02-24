import os
import click

def init(app):

	# removes the 'pkg-resources=0.0.0' bug with ubuntu
	@app.cli.command()
	def freeze():
		os.system('pip freeze > requirements.txt')
		os.system('sed "/pkg-resources==0.0.0" requirements.txt')
