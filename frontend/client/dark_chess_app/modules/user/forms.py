from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired

class UserSearchForm(FlaskForm):

	username = StringField('username', validators=[InputRequired()])