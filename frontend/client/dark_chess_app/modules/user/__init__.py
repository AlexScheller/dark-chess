from flask import Blueprint

user = Blueprint('user', __name__)

from dark_chess_app.modules.user import routes