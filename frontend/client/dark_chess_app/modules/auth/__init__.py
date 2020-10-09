from flask import Blueprint

auth = Blueprint('auth', __name__)

from dark_chess_app.modules.auth import routes