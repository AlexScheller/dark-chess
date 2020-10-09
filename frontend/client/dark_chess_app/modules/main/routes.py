from flask import render_template
from flask_login import current_user
from dark_chess_app.modules.main import main
from dark_chess_app.modules.auth.forms import LoginForm

@main.route('/')
@main.route('/index')
def index():
	if not current_user.is_authenticated:
		form = LoginForm()
		return render_template('main/index.html', form=form)
	return render_template('main/index.html')