from flask import render_template
from dark_chess_app.modules.main import main

@main.route('/')
@main.route('/index')
def index():
	return render_template('main/index.html')