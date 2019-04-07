import requests
from flask import render_template, flash, url_for, redirect
from dark_chess_app.modules.auth import auth
from dark_chess_app.modules.auth.forms import RegistrationForm
from dark_chess_app.utilities.api_utilities import api_request

@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		reg_res = api_request(requests.post,
			'/user/auth/register',
			json={
				'username': form.username.data,
				'password': form.password.data
			}
		)
		if reg_res.status_code == 200:
			flash('Successfully registered!', 'success')
			return redirect(url_for('main.index'))
		flash('Failed to register...', 'error')
		return redirect(url_for('main.index'))
	return render_template('auth/register.html',
		title='Sign Up',
		form=form
	)