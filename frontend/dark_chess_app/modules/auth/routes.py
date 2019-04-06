import requests
from flask import render_template
from dark_chess_app.modules import auth
from dark_chess_app.modules.auth.forms import RegistrationForm

@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		return 'Valid'
	return render_template('auth/register.html',
		title='Sign Up',
		form=form
	)