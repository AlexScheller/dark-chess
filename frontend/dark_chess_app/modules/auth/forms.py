from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email

class RegistrationForm(FlaskForm):

	username = StringField('username', validators=[InputRequired()])
	email = StringField('email', validators=[
		InputRequired(),
		Email()
	])
	password = PasswordField('password', validators=[InputRequired()])
	# For invite-only period, should be removed once that's over.
	beta_code = StringField('Invite Code', validators=[InputRequired()])
	first_name = StringField('first name') # honey pot

class LoginForm(FlaskForm):

	username = StringField('username', validators=[InputRequired()])
	password = PasswordField('password', validators=[InputRequired()])
	remember_me = BooleanField('keep me signed in')