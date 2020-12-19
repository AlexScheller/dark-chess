from flask import render_template
from flask_login import current_user, login_required
from dark_chess_app.modules.main import main
from dark_chess_app.modules.auth.forms import LoginForm

@main.route('/')
@main.route('/index')
def index():
	if not current_user.is_authenticated:
		form = LoginForm()
		return render_template('main/index.html', form=form)
	return render_template('main/index.html')

@main.route('/about')
@login_required
def about():
	return render_template('main/about.html')

@main.route('/version-history')
@login_required
def version_history():
	return render_template('main/version_history.html')