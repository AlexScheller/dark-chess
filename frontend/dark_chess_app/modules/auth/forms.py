from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField

class RegistrationForm(FlaskForm):

	username = StringField('username')
	email = StringField('email')
	password = PasswordField('password')