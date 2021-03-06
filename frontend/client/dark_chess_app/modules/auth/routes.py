import requests

from flask import render_template, flash, url_for, redirect, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from dark_chess_app.modules.auth import auth
from dark_chess_app.modules.auth.session_model import User
from dark_chess_app.modules.auth.forms import RegistrationForm, LoginForm
from dark_chess_app.utilities.api_utilities import api_request

@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		if form.first_name.data != '': # honey pot
			return redirect(url_for('main.index'))
		reg_res = api_request('/user/auth/register',
			method=requests.post,
			json={
				'username': form.username.data,
				'email': form.email.data,
				'password': form.password.data,
				'password_confirmed': form.password_confirmation.data,
				'beta_code': form.beta_code.data
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

@auth.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		flash('You are already logged in')
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		token_res = api_request('/user/auth/token',
			auth=(form.username.data, form.password.data)
		)
		if token_res.status_code == 200:
			token_json = token_res.json()
			user = User(token_json['token'],
				user_data=token_json['user']
			)
			login_user(user, remember=form.remember_me.data)
			flash('Successfully logged in', 'success')
			# Inserted by `@login_required` for redirection.
			next_page = request.args.get('next')
			# Handle attempts to redirect outside the application
			if next_page is not None and url_parse(next_page).netloc == '':
				return redirect(next_page)
			return redirect(url_for('main.index'))
		flash('Login unsuccessful', 'error')
		return redirect(url_for('auth.login'))
	return render_template('auth/login.html',
		title='Login',
		form=form
	)

@auth.route('/logout')
def logout():
	if current_user.is_authenticated:
		logout_user()
	return redirect(url_for('main.index'))
